"""Search panel for the Car Search application.

This module provides a panel for inputting search parameters.
"""

import json
import os
import re
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config.manager import config_manager
from ..core.logging import get_logger
from ..data.car_service import car_service

# Set up logger for this module
logger = get_logger(__name__)

# Directory for saving search parameters
SAVED_SEARCHES_DIR = Path.home() / ".car_search" / "saved_searches"


class SearchPanel(QWidget):
    """Panel for inputting search parameters."""

    # Signal emitted when search is triggered
    search_triggered = pyqtSignal(dict)

    def __init__(self, parent=None):
        """Initialize the search panel."""
        super().__init__(parent)

        # Log initialization
        logger.info("Initializing search panel")

        # Initialize saved searches directory
        self.saved_searches_dir = Path.home() / ".car_search" / "saved_searches"
        self.saved_searches_dir.mkdir(parents=True, exist_ok=True)

        # Initialize UI components
        self._init_ui()

        # Load last used search parameters
        self._load_last_search()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Search Parameters")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Location parameters
        location_group = QGroupBox("Location")
        location_layout = QGridLayout(location_group)

        location_layout.addWidget(QLabel("Postcode:"), 0, 0)
        self.postcode_input = QLineEdit()
        self.postcode_input.setPlaceholderText("e.g. M1 1AA")
        # Add validation feedback on edit
        self.postcode_input.textChanged.connect(self._validate_postcode)

        # Add validation status label
        self.postcode_validation = QLabel("")
        self.postcode_validation.setStyleSheet("color: red; font-size: 10px;")

        location_layout.addWidget(self.postcode_input, 0, 1)
        location_layout.addWidget(self.postcode_validation, 1, 0, 1, 2)

        location_layout.addWidget(QLabel("Radius (miles):"), 2, 0)
        self.radius_input = QSpinBox()
        self.radius_input.setRange(5, 200)
        self.radius_input.setSingleStep(5)
        self.radius_input.setValue(config_manager.get_setting("search.default_radius"))
        location_layout.addWidget(self.radius_input, 2, 1)

        layout.addWidget(location_group)

        # Price parameters
        price_group = QGroupBox("Price")
        price_layout = QGridLayout(price_group)

        price_layout.addWidget(QLabel("Min Price (£):"), 0, 0)
        self.min_price_input = QSpinBox()
        self.min_price_input.setRange(0, 100000)
        self.min_price_input.setSingleStep(500)
        self.min_price_input.setValue(0)
        # Connect to validation method
        self.min_price_input.valueChanged.connect(self._validate_price_range)
        price_layout.addWidget(self.min_price_input, 0, 1)

        price_layout.addWidget(QLabel("Max Price (£):"), 1, 0)
        self.max_price_input = QSpinBox()
        self.max_price_input.setRange(500, 1000000)
        self.max_price_input.setSingleStep(500)
        self.max_price_input.setValue(config_manager.get_setting("search.default_max_price"))
        # Connect to validation method
        self.max_price_input.valueChanged.connect(self._validate_price_range)
        price_layout.addWidget(self.max_price_input, 1, 1)

        # Add price validation status label
        self.price_validation = QLabel("")
        self.price_validation.setStyleSheet("color: red; font-size: 10px;")
        price_layout.addWidget(self.price_validation, 2, 0, 1, 2)

        layout.addWidget(price_group)

        # Car parameters
        car_group = QGroupBox("Car Details")
        car_layout = QGridLayout(car_group)

        car_layout.addWidget(QLabel("Make:"), 0, 0)
        self.make_input = QComboBox()
        self.make_input.addItem("Any")
        self._populate_makes()
        car_layout.addWidget(self.make_input, 0, 1)

        car_layout.addWidget(QLabel("Model:"), 1, 0)
        self.model_input = QComboBox()
        self.model_input.addItem("Any")
        car_layout.addWidget(self.model_input, 1, 1)

        car_layout.addWidget(QLabel("Transmission:"), 2, 0)
        self.transmission_input = QComboBox()
        self.transmission_input.addItems(["Any", "Automatic", "Manual"])
        car_layout.addWidget(self.transmission_input, 2, 1)

        car_layout.addWidget(QLabel("Fuel Type:"), 3, 0)
        self.fuel_type_input = QComboBox()
        self.fuel_type_input.addItems(["Any", "Petrol", "Diesel", "Hybrid", "Electric"])
        car_layout.addWidget(self.fuel_type_input, 3, 1)

        car_layout.addWidget(QLabel("Body Style:"), 4, 0)
        self.body_style_input = QComboBox()
        self.body_style_input.addItems(["Any", "Hatchback", "Saloon", "Estate", "SUV", "Convertible", "Coupe", "Van"])
        car_layout.addWidget(self.body_style_input, 4, 1)

        car_layout.addWidget(QLabel("Color:"), 5, 0)
        self.color_input = QComboBox()
        self.color_input.addItems([
            "Any",
            "Black",
            "White",
            "Silver",
            "Grey",
            "Blue",
            "Red",
            "Green",
            "Yellow",
            "Orange",
            "Brown",
        ])
        car_layout.addWidget(self.color_input, 5, 1)

        # Year range
        car_layout.addWidget(QLabel("Year Min:"), 6, 0)
        self.year_min_input = QSpinBox()
        self.year_min_input.setRange(1980, 2030)
        self.year_min_input.setValue(2010)
        car_layout.addWidget(self.year_min_input, 6, 1)

        car_layout.addWidget(QLabel("Year Max:"), 7, 0)
        self.year_max_input = QSpinBox()
        self.year_max_input.setRange(1980, 2030)
        self.year_max_input.setValue(2023)
        car_layout.addWidget(self.year_max_input, 7, 1)

        # Mileage
        car_layout.addWidget(QLabel("Max Mileage:"), 8, 0)
        self.mileage_max_input = QSpinBox()
        self.mileage_max_input.setRange(0, 200000)
        self.mileage_max_input.setSingleStep(1000)
        self.mileage_max_input.setValue(100000)
        car_layout.addWidget(self.mileage_max_input, 8, 1)

        # Zip code input
        car_layout.addWidget(QLabel("Zip Code:"), 9, 0)
        self.zip_input = QLineEdit()
        self.zip_input.setPlaceholderText("Enter zip code")
        car_layout.addWidget(self.zip_input, 9, 1)

        # Checkboxes
        car_layout.addWidget(QLabel("Certified:"), 10, 0)
        self.certified_input = QCheckBox()
        car_layout.addWidget(self.certified_input, 10, 1)

        car_layout.addWidget(QLabel("No Accidents:"), 11, 0)
        self.no_accidents_input = QCheckBox()
        car_layout.addWidget(self.no_accidents_input, 11, 1)

        # Distance input
        car_layout.addWidget(QLabel("Within Miles:"), 12, 0)
        self.distance_input = QSpinBox()
        self.distance_input.setRange(5, 500)
        self.distance_input.setSingleStep(5)
        self.distance_input.setValue(50)
        car_layout.addWidget(self.distance_input, 12, 1)

        layout.addWidget(car_group)

        # Saved searches buttons
        saved_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Search")
        self.save_button.clicked.connect(self._save_search)
        saved_layout.addWidget(self.save_button)

        self.load_button = QPushButton("Load Search")
        self.load_button.clicked.connect(self._load_search_dialog)
        saved_layout.addWidget(self.load_button)

        layout.addLayout(saved_layout)

        # Spacer to push content to the top
        layout.addStretch(1)

        # Search button
        self.search_button = QPushButton("Search Cars")
        self.search_button.clicked.connect(self._on_search)
        layout.addWidget(self.search_button)

        # Initial validation
        self._validate_postcode()
        self._validate_price_range()

        # Implement the _on_make_changed method to update models list
        self.make_input.currentTextChanged.connect(self._on_make_changed)

    def _validate_postcode(self):
        """Validate the postcode input."""
        postcode = self.postcode_input.text().strip().upper()

        # Allow empty postcode (nationwide search)
        if not postcode:
            self.postcode_validation.setText("")
            self.postcode_input.setStyleSheet("")
            return True

        # UK postcode regex pattern - basic validation
        # Full validation would require additional checks
        pattern = r"^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$"
        is_valid = bool(re.match(pattern, postcode))

        if is_valid:
            self.postcode_validation.setText("")
            self.postcode_input.setStyleSheet("border: 1px solid green;")
            return True
        else:
            self.postcode_validation.setText("Please enter a valid UK postcode (e.g. M1 1AA)")
            self.postcode_input.setStyleSheet("border: 1px solid red;")
            return False

    def _validate_price_range(self):
        """Validate the price range inputs."""
        min_price = self.min_price_input.value()
        max_price = self.max_price_input.value()

        if min_price >= max_price:
            self.price_validation.setText("Min price must be less than max price")
            self.min_price_input.setStyleSheet("border: 1px solid red;")
            self.max_price_input.setStyleSheet("border: 1px solid red;")
            return False
        else:
            self.price_validation.setText("")
            self.min_price_input.setStyleSheet("")
            self.max_price_input.setStyleSheet("")
            return True

    def _validate_form(self):
        """Validate the complete form before search.

        Returns:
            bool: True if valid, False otherwise
        """
        valid_postcode = self._validate_postcode()
        valid_prices = self._validate_price_range()

        return valid_postcode and valid_prices

    def _populate_makes(self):
        """Populate the makes dropdown with available car makes."""
        try:
            # Try to get makes from car service
            makes = car_service.get_makes()
            if makes:
                self.make_input.clear()
                self.make_input.addItem("Any")
                self.make_input.addItems(makes)
                logger.info(f"Populated {len(makes)} car makes")
            else:
                logger.warning("No car makes found from API")
        except Exception as e:
            logger.error(f"Error populating car makes: {e}")

    def _save_search(self):
        """Save the current search parameters."""
        # Get parameters to save
        params = self.get_search_parameters()

        # Ask for a name to save as
        name, ok = QInputDialog.getText(
            self,
            "Save Search",
            "Enter a name for this search:",
            QLineEdit.EchoMode.Normal,
            f"Search {len(os.listdir(SAVED_SEARCHES_DIR)) + 1}",
        )

        if not ok or not name:
            return

        # Create a safe filename
        filename = name.replace(" ", "_").replace("/", "_").replace("\\", "_") + ".json"
        filepath = SAVED_SEARCHES_DIR / filename

        try:
            with open(filepath, "w") as f:
                json.dump({"name": name, "parameters": params}, f, indent=2)

            logger.info(f"Saved search parameters to {filepath}")
            QMessageBox.information(
                self, "Search Saved", f"Search parameters saved as '{name}'", QMessageBox.StandardButton.Ok
            )

            # Also save as last search
            self._save_last_search()

        except Exception as e:
            logger.error(f"Error saving search parameters: {e}")
            QMessageBox.warning(
                self, "Save Failed", f"Could not save search parameters: {e}", QMessageBox.StandardButton.Ok
            )

    def _load_search_dialog(self):
        """Show dialog to load a saved search."""
        # Get list of saved searches
        try:
            saved_searches = []
            for filepath in SAVED_SEARCHES_DIR.glob("*.json"):
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                        saved_searches.append((data.get("name", filepath.stem), str(filepath)))
                except:
                    pass

            if not saved_searches:
                QMessageBox.information(
                    self, "No Saved Searches", "No saved searches found.", QMessageBox.StandardButton.Ok
                )
                return

            # Show dialog to select a search
            selection, ok = QInputDialog.getItem(
                self, "Load Search", "Select a saved search:", [name for name, _ in saved_searches], 0, False
            )

            if not ok or not selection:
                return

            # Get filepath for selected search
            filepath = next((path for name, path in saved_searches if name == selection), None)
            if not filepath:
                return

            # Load and apply the search parameters
            self._load_search_from_file(filepath)

        except Exception as e:
            logger.error(f"Error loading saved searches: {e}")
            QMessageBox.warning(
                self, "Load Failed", f"Could not load saved searches: {e}", QMessageBox.StandardButton.Ok
            )

    def _load_search_from_file(self, filepath):
        """Load and apply search parameters from a file.

        Args:
            filepath: Path to the saved search file
        """
        try:
            with open(filepath) as f:
                data = json.load(f)

            params = data.get("parameters", {})
            if params:
                self.set_search_parameters(params)
                logger.info(f"Loaded search parameters from {filepath}")

                # Save as last search
                self._save_last_search()

        except Exception as e:
            logger.error(f"Error loading search parameters: {e}")
            QMessageBox.warning(
                self, "Load Failed", f"Could not load search parameters: {e}", QMessageBox.StandardButton.Ok
            )

    def _save_last_search(self):
        """Save the current search parameters as the last used search."""
        try:
            params = self.get_search_parameters()
            filepath = SAVED_SEARCHES_DIR / "last_search.json"

            with open(filepath, "w") as f:
                json.dump({"name": "Last Search", "parameters": params}, f, indent=2)

            logger.info(f"Saved last search parameters to {filepath}")

        except Exception as e:
            logger.error(f"Error saving last search parameters: {e}")

    def _load_last_search(self):
        """Load the last used search parameters if available."""
        filepath = SAVED_SEARCHES_DIR / "last_search.json"
        if filepath.exists():
            try:
                self._load_search_from_file(filepath)
            except Exception as e:
                logger.error(f"Error loading last search parameters: {e}")

    def _on_search(self):
        """Handle search button click."""
        # Validate form before proceeding
        if not self._validate_form():
            logger.warning("Search attempted with invalid form data")
            QMessageBox.warning(
                self,
                "Invalid Search Parameters",
                "Please correct the highlighted fields before searching.",
                QMessageBox.StandardButton.Ok,
            )
            return

        # Get search parameters
        search_params = self.get_search_parameters()

        # Log search parameters
        logger.info(
            f"Search requested: postcode={search_params['postcode']}, "
            f"radius={search_params['radius']}, "
            f"price={search_params['min_price']}-{search_params['max_price']}, "
            f"make={search_params['make']}, "
            f"transmission={search_params['transmission']}"
        )

        # Save as last search
        self._save_last_search()

        # Emit signal with search parameters
        self.search_triggered.emit(search_params)

    def get_search_parameters(self):
        """Get the current search parameters.

        Returns:
            dict: Current search parameters
        """
        return {
            "postcode": self.postcode_input.text().strip().upper(),
            "radius": self.radius_input.value(),
            "min_price": self.min_price_input.value(),
            "max_price": self.max_price_input.value(),
            "make": self.make_input.currentText(),
            "transmission": self.transmission_input.currentText(),
        }

    def set_search_parameters(self, params):
        """Set search parameters.

        Args:
            params (dict): Search parameters to set
        """
        if "postcode" in params:
            self.postcode_input.setText(params["postcode"])
        if "radius" in params:
            self.radius_input.setValue(params["radius"])
        if "min_price" in params:
            self.min_price_input.setValue(params["min_price"])
        if "max_price" in params:
            self.max_price_input.setValue(params["max_price"])
        if "make" in params:
            index = self.make_input.findText(params["make"])
            if index >= 0:
                self.make_input.setCurrentIndex(index)
        if "transmission" in params:
            index = self.transmission_input.findText(params["transmission"])
            if index >= 0:
                self.transmission_input.setCurrentIndex(index)

    def _save_search_state(self, name=None):
        """Save the current search state to a file."""
        try:
            # Get the current state
            state = self._get_current_search_state()

            # If no name provided, prompt the user
            if not name:
                name, ok = QInputDialog.getText(self, "Save Search", "Enter a name for this search:", QLineEdit.Normal)
                if not ok or not name:
                    return

            # Create a valid filename
            filename = f"{name.replace(' ', '_')}.json"
            filepath = os.path.join(self.saved_searches_dir, filename)

            # Write the state to file
            with open(filepath, "w") as f:
                json.dump(state, f, indent=4)

            # Also save as last_search.json
            last_search_path = os.path.join(self.saved_searches_dir, "last_search.json")
            with open(last_search_path, "w") as f:
                json.dump(state, f, indent=4)

            logger.info(f"Search state saved to: {filepath}")
            QMessageBox.information(self, "Search Saved", f"Search saved as '{name}'")

        except Exception as e:
            logger.error(f"Failed to save search state: {e}")
            QMessageBox.warning(self, "Save Failed", f"Failed to save search: {e!s}")

    def _load_search_state(self):
        """Load a saved search state."""
        try:
            # Get list of saved searches
            search_files = [
                f for f in os.listdir(self.saved_searches_dir) if f.endswith(".json") and f != "last_search.json"
            ]

            if not search_files:
                QMessageBox.information(self, "No Saved Searches", "No saved searches found.")
                return

            # Create a dialog with a list widget
            dialog = QDialog(self)
            dialog.setWindowTitle("Select a Saved Search")
            dialog.setMinimumWidth(300)

            layout = QVBoxLayout(dialog)
            list_widget = QListWidget()

            # Add items to the list, removing .json extension and converting underscores to spaces
            for file in search_files:
                display_name = file[:-5].replace("_", " ")  # Remove .json and convert _ to space
                list_widget.addItem(display_name)

            layout.addWidget(list_widget)

            # Add buttons
            button_layout = QHBoxLayout()
            load_button = QPushButton("Load")
            cancel_button = QPushButton("Cancel")

            button_layout.addWidget(load_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)

            # Connect signals
            load_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)

            # Show dialog and get result
            if dialog.exec_() == QDialog.Accepted and list_widget.currentItem():
                selected_name = list_widget.currentItem().text()
                filename = f"{selected_name.replace(' ', '_')}.json"
                filepath = os.path.join(self.saved_searches_dir, filename)

                # Load the state from file
                with open(filepath) as f:
                    state = json.load(f)

                # Apply the state
                self._apply_search_state(state)
                logger.info(f"Loaded search state from: {filepath}")

        except Exception as e:
            logger.error(f"Failed to load search state: {e}")
            QMessageBox.warning(self, "Load Failed", f"Failed to load search: {e!s}")

    def _try_load_last_search(self):
        """Try to load the last search state if it exists."""
        try:
            last_search_path = os.path.join(self.saved_searches_dir, "last_search.json")
            if os.path.exists(last_search_path):
                with open(last_search_path) as f:
                    state = json.load(f)
                self._apply_search_state(state)
                logger.info("Loaded last search state")
        except Exception as e:
            logger.error(f"Failed to load last search state: {e}")

    def _get_current_search_state(self):
        """Get the current search state as a dictionary."""
        return {
            "make": self.make_input.currentText(),
            "model": self.model_input.currentText(),
            "year_min": self.year_min_input.value(),
            "year_max": self.year_max_input.value(),
            "price_min": self.price_min_input.value(),
            "price_max": self.price_max_input.value(),
            "mileage_max": self.mileage_max_input.value(),
            "transmission": self.transmission_input.currentText(),
            "fuel_type": self.fuel_type_input.currentText(),
            "body_style": self.body_style_input.currentText(),
            "color": self.color_input.currentText(),
            "within_miles": self.distance_input.value(),
            "zip_code": self.zip_input.text(),
            "certified": self.certified_input.isChecked(),
            "no_accidents": self.no_accidents_input.isChecked(),
        }

    def _apply_search_state(self, search_state):
        """Apply a saved search state to the current UI."""
        # Set make
        make = search_state.get("make", "")
        if make:
            index = self.make_input.findText(make)
            if index >= 0:
                self.make_input.setCurrentIndex(index)
                self._on_make_changed(make)  # Update models list

        # After models are loaded, set model
        model = search_state.get("model", "")
        if model:
            index = self.model_input.findText(model)
            if index >= 0:
                self.model_input.setCurrentIndex(index)

        # Set numeric inputs
        self.year_min_input.setValue(search_state.get("year_min", self.year_min_input.minimum()))
        self.year_max_input.setValue(search_state.get("year_max", self.year_max_input.maximum()))
        self.price_min_input.setValue(search_state.get("price_min", self.price_min_input.minimum()))
        self.price_max_input.setValue(search_state.get("price_max", self.price_max_input.maximum()))
        self.mileage_max_input.setValue(search_state.get("mileage_max", self.mileage_max_input.maximum()))
        self.distance_input.setValue(search_state.get("within_miles", self.distance_input.value()))

        # Set text inputs
        self.zip_input.setText(search_state.get("zip_code", ""))

        # Set dropdowns
        transmission = search_state.get("transmission", "")
        if transmission:
            index = self.transmission_input.findText(transmission)
            if index >= 0:
                self.transmission_input.setCurrentIndex(index)

        fuel_type = search_state.get("fuel_type", "")
        if fuel_type:
            index = self.fuel_type_input.findText(fuel_type)
            if index >= 0:
                self.fuel_type_input.setCurrentIndex(index)

        body_style = search_state.get("body_style", "")
        if body_style:
            index = self.body_style_input.findText(body_style)
            if index >= 0:
                self.body_style_input.setCurrentIndex(index)

        color = search_state.get("color", "")
        if color:
            index = self.color_input.findText(color)
            if index >= 0:
                self.color_input.setCurrentIndex(index)

        # Set checkboxes
        self.certified_input.setChecked(search_state.get("certified", False))
        self.no_accidents_input.setChecked(search_state.get("no_accidents", False))

    def _on_make_changed(self, make):
        """Update the models dropdown when make changes.

        Args:
            make (str): The selected car make
        """
        try:
            # Clear current models
            self.model_input.clear()
            self.model_input.addItem("Any")

            # If "Any" is selected, don't populate models
            if make == "Any":
                return

            # Try to get models from car service
            models = car_service.get_models(make)
            if models:
                self.model_input.addItems(models)
                logger.info(f"Populated {len(models)} models for {make}")
            else:
                logger.warning(f"No models found for make: {make}")
        except Exception as e:
            logger.error(f"Error populating models for {make}: {e}")
