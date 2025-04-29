"""Results view for the Car Search application.

This module provides a view for displaying search results.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.logging import get_logger

# Set up logger for this module
logger = get_logger(__name__)


class ResultsView(QWidget):
    """View for displaying search results."""

    # Signal emitted when a car is selected
    car_selected = pyqtSignal(dict)

    def __init__(self):
        """Initialize the results view."""
        super().__init__()

        # Log initialization
        logger.info("Initializing results view")

        # Store the current result data and filtered data
        self.result_data = []
        self.filtered_data = []

        # Current sort column and order
        self.sort_column = 0  # Default: sort by make/model
        self.sort_order = Qt.SortOrder.AscendingOrder

        # Filter settings
        self.filters = {
            "make": "Any",
            "transmission": "Any",
            "min_price": 0,
            "max_price": 1000000,
            "min_year": 0,
            "max_year": 3000,
        }

        # Track whether filters are visible
        self.filters_visible = False

        # Initialize UI components
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Results count and sorting controls
        header_layout = QHBoxLayout()

        # Results count label
        self.results_count_label = QLabel("0 results found")
        header_layout.addWidget(self.results_count_label)

        header_layout.addStretch(1)

        # Filter toggle button
        self.filter_button = QPushButton("Filters ▼")
        self.filter_button.clicked.connect(self._toggle_filters)
        header_layout.addWidget(self.filter_button)

        # Sorting controls
        sort_label = QLabel("Sort by:")
        header_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Make/Model", "Year", "Price", "Mileage", "Location", "Score"])
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        header_layout.addWidget(self.sort_combo)

        self.sort_order_button = QPushButton("↑")
        self.sort_order_button.setFixedWidth(30)
        self.sort_order_button.clicked.connect(self._toggle_sort_order)
        header_layout.addWidget(self.sort_order_button)

        layout.addLayout(header_layout)

        # Filters section (initially hidden)
        self.filters_group = QGroupBox("Filters")
        self.filters_group.setVisible(False)
        filters_layout = QGridLayout(self.filters_group)

        # Make filter
        filters_layout.addWidget(QLabel("Make:"), 0, 0)
        self.make_filter = QComboBox()
        self.make_filter.addItem("Any")
        self.make_filter.currentTextChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.make_filter, 0, 1)

        # Transmission filter
        filters_layout.addWidget(QLabel("Transmission:"), 0, 2)
        self.transmission_filter = QComboBox()
        self.transmission_filter.addItems(["Any", "Automatic", "Manual"])
        self.transmission_filter.currentTextChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.transmission_filter, 0, 3)

        # Price range filter
        filters_layout.addWidget(QLabel("Price Range:"), 1, 0)
        price_layout = QHBoxLayout()

        self.min_price_filter = QSpinBox()
        self.min_price_filter.setRange(0, 1000000)
        self.min_price_filter.setSingleStep(1000)
        self.min_price_filter.setValue(0)
        self.min_price_filter.valueChanged.connect(self._apply_filters)
        price_layout.addWidget(self.min_price_filter)

        price_layout.addWidget(QLabel("to"))

        self.max_price_filter = QSpinBox()
        self.max_price_filter.setRange(0, 1000000)
        self.max_price_filter.setSingleStep(1000)
        self.max_price_filter.setValue(1000000)
        self.max_price_filter.valueChanged.connect(self._apply_filters)
        price_layout.addWidget(self.max_price_filter)

        filters_layout.addLayout(price_layout, 1, 1, 1, 3)

        # Year range filter
        filters_layout.addWidget(QLabel("Year Range:"), 2, 0)
        year_layout = QHBoxLayout()

        self.min_year_filter = QSpinBox()
        self.min_year_filter.setRange(1970, 2030)
        self.min_year_filter.setValue(1970)
        self.min_year_filter.valueChanged.connect(self._apply_filters)
        year_layout.addWidget(self.min_year_filter)

        year_layout.addWidget(QLabel("to"))

        self.max_year_filter = QSpinBox()
        self.max_year_filter.setRange(1970, 2030)
        self.max_year_filter.setValue(2030)
        self.max_year_filter.valueChanged.connect(self._apply_filters)
        year_layout.addWidget(self.max_year_filter)

        filters_layout.addLayout(year_layout, 2, 1, 1, 3)

        # Reset filters button
        self.reset_filters_button = QPushButton("Reset Filters")
        self.reset_filters_button.clicked.connect(self._reset_filters)
        filters_layout.addWidget(self.reset_filters_button, 3, 3)

        layout.addWidget(self.filters_group)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(["Make/Model", "Year", "Price", "Mileage", "Location", "Score"])

        # Enable sorting when clicking on headers
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        # Set column widths
        self.results_table.setColumnWidth(0, 200)  # Make/Model
        self.results_table.setColumnWidth(1, 70)  # Year
        self.results_table.setColumnWidth(2, 100)  # Price
        self.results_table.setColumnWidth(3, 100)  # Mileage
        self.results_table.setColumnWidth(4, 150)  # Location
        self.results_table.setColumnWidth(5, 70)  # Score

        # Connect signals
        self.results_table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.results_table)

    def _toggle_filters(self):
        """Toggle the visibility of the filters section."""
        self.filters_visible = not self.filters_visible
        self.filters_group.setVisible(self.filters_visible)

        # Update button text
        if self.filters_visible:
            self.filter_button.setText("Filters ▲")
        else:
            self.filter_button.setText("Filters ▼")

    def _reset_filters(self):
        """Reset all filters to their default values."""
        self.make_filter.setCurrentText("Any")
        self.transmission_filter.setCurrentText("Any")
        self.min_price_filter.setValue(0)
        self.max_price_filter.setValue(1000000)
        self.min_year_filter.setValue(1970)
        self.max_year_filter.setValue(2030)

        # Update filters
        self.filters = {
            "make": "Any",
            "transmission": "Any",
            "min_price": 0,
            "max_price": 1000000,
            "min_year": 1970,
            "max_year": 2030,
        }

        # Apply filters (should show all results)
        self._apply_filters()

    def _apply_filters(self):
        """Apply the current filters to the results data."""
        # Update filter settings
        self.filters = {
            "make": self.make_filter.currentText(),
            "transmission": self.transmission_filter.currentText(),
            "min_price": self.min_price_filter.value(),
            "max_price": self.max_price_filter.value(),
            "min_year": self.min_year_filter.value(),
            "max_year": self.max_year_filter.value(),
        }

        # Filter the data
        self.filtered_data = []
        for car in self.result_data:
            # Check make filter
            if self.filters["make"] != "Any" and car["make"] != self.filters["make"]:
                continue

            # Check transmission filter
            if self.filters["transmission"] != "Any":
                car_transmission = car.get("data", {}).get("transmission", "")
                if self.filters["transmission"].lower() not in car_transmission.lower():
                    continue

            # Check price range
            if car["price"] < self.filters["min_price"] or car["price"] > self.filters["max_price"]:
                continue

            # Check year range
            if car["year"] < self.filters["min_year"] or car["year"] > self.filters["max_year"]:
                continue

            # All filters passed, add to filtered data
            self.filtered_data.append(car)

        # Apply the current sort to the filtered data
        self._apply_sort()

        logger.debug(f"Applied filters: {len(self.filtered_data)} results from {len(self.result_data)} total")

    def _on_sort_changed(self, index):
        """Handle changes to the sort column.

        Args:
            index: The index of the selected sort column
        """
        self.sort_column = index
        self._apply_sort()

    def _toggle_sort_order(self):
        """Toggle between ascending and descending sort order."""
        if self.sort_order == Qt.SortOrder.AscendingOrder:
            self.sort_order = Qt.SortOrder.DescendingOrder
            self.sort_order_button.setText("↓")
        else:
            self.sort_order = Qt.SortOrder.AscendingOrder
            self.sort_order_button.setText("↑")

        self._apply_sort()

    def _on_header_clicked(self, logical_index):
        """Handle clicking on table headers for sorting.

        Args:
            logical_index: The index of the clicked column
        """
        # Update sort combobox to match clicked column
        self.sort_combo.setCurrentIndex(logical_index)

        # If clicking the same column, toggle sort order
        if self.sort_column == logical_index:
            self._toggle_sort_order()
        else:
            # New column, use ascending order
            self.sort_column = logical_index
            self.sort_order = Qt.SortOrder.AscendingOrder
            self.sort_order_button.setText("↑")
            self._apply_sort()

    def _apply_sort(self):
        """Apply the current sort settings to the filtered data."""
        if not self.filtered_data:
            return

        # Disable sorting temporarily to avoid triggering multiple sorts
        self.results_table.setSortingEnabled(False)

        # Sort the data based on the selected column and order
        if self.sort_column == 0:  # Make/Model
            self.filtered_data.sort(
                key=lambda x: f"{x['make']} {x['model']}", reverse=(self.sort_order == Qt.SortOrder.DescendingOrder)
            )
        elif self.sort_column == 1:  # Year
            self.filtered_data.sort(key=lambda x: x["year"], reverse=(self.sort_order == Qt.SortOrder.DescendingOrder))
        elif self.sort_column == 2:  # Price
            self.filtered_data.sort(key=lambda x: x["price"], reverse=(self.sort_order == Qt.SortOrder.DescendingOrder))
        elif self.sort_column == 3:  # Mileage
            self.filtered_data.sort(
                key=lambda x: x["mileage"], reverse=(self.sort_order == Qt.SortOrder.DescendingOrder)
            )
        elif self.sort_column == 4:  # Location
            self.filtered_data.sort(
                key=lambda x: x["location"], reverse=(self.sort_order == Qt.SortOrder.DescendingOrder)
            )
        elif self.sort_column == 5:  # Score
            self.filtered_data.sort(key=lambda x: x["score"], reverse=(self.sort_order == Qt.SortOrder.DescendingOrder))

        # Update the table with the sorted data
        self._populate_table()

        # Re-enable sorting
        self.results_table.setSortingEnabled(True)

        logger.debug(
            f"Applied sort: column={self.sort_column}, order={'descending' if self.sort_order == Qt.SortOrder.DescendingOrder else 'ascending'}"
        )

    def _populate_table(self):
        """Populate the table with the current filtered data."""
        # Clear existing data
        self.results_table.setRowCount(0)

        if not self.filtered_data:
            self.results_count_label.setText("0 results found")
            return

        # Add rows
        self.results_table.setRowCount(len(self.filtered_data))

        for row, car in enumerate(self.filtered_data):
            # Store the complete car data in the first cell's user data
            make_model_item = QTableWidgetItem(f"{car['make']} {car['model']}")
            make_model_item.setData(Qt.ItemDataRole.UserRole, car)
            self.results_table.setItem(row, 0, make_model_item)

            # Year
            year_item = QTableWidgetItem(str(car["year"]))
            self.results_table.setItem(row, 1, year_item)

            # Price
            price_item = QTableWidgetItem(f"£{car['price']:,}")
            # Store the numeric price for sorting
            price_item.setData(Qt.ItemDataRole.UserRole, car["price"])
            self.results_table.setItem(row, 2, price_item)

            # Mileage
            mileage_item = QTableWidgetItem(f"{car['mileage']:,} mi")
            # Store the numeric mileage for sorting
            mileage_item.setData(Qt.ItemDataRole.UserRole, car["mileage"])
            self.results_table.setItem(row, 3, mileage_item)

            # Location
            location_item = QTableWidgetItem(car["location"])
            self.results_table.setItem(row, 4, location_item)

            # Score
            score_item = QTableWidgetItem(f"{car['score']:.1f}")
            # Store the numeric score for sorting
            score_item.setData(Qt.ItemDataRole.UserRole, car["score"])

            # Color code the score: green for >8, yellow for 7-8, red for <7
            if car["score"] > 8:
                score_item.setBackground(QColor(200, 255, 200))  # Light green
            elif car["score"] >= 7:
                score_item.setBackground(QColor(255, 255, 200))  # Light yellow
            else:
                score_item.setBackground(QColor(255, 200, 200))  # Light red
            self.results_table.setItem(row, 5, score_item)

        # Update count label
        if len(self.filtered_data) == len(self.result_data):
            self.results_count_label.setText(f"{len(self.filtered_data)} results found")
        else:
            self.results_count_label.setText(f"{len(self.filtered_data)} of {len(self.result_data)} results shown")

    def _update_filter_options(self):
        """Update the filter options based on the available data."""
        if not self.result_data:
            return

        # Get unique makes
        makes = sorted(set(car["make"] for car in self.result_data))

        # Update make filter options while preserving current selection
        current_make = self.make_filter.currentText()
        self.make_filter.clear()
        self.make_filter.addItem("Any")
        self.make_filter.addItems(makes)

        # Try to restore previous selection
        index = self.make_filter.findText(current_make)
        if index >= 0:
            self.make_filter.setCurrentIndex(index)

    def add_test_data(self):
        """Add test data to the results table."""
        # Test data
        self.result_data = [
            {
                "make": "Toyota",
                "model": "Corolla",
                "year": 2018,
                "price": 14995,
                "mileage": 35000,
                "location": "Manchester",
                "score": 8.5,
                "data": {
                    "id": "TC001",
                    "engine": "1.8L Hybrid",
                    "transmission": "Automatic",
                    "color": "Silver",
                    "fuel_type": "Hybrid",
                    "mpg": 62,
                    "body_type": "Hatchback",
                    "reliability_score": 4.5,
                },
            },
            {
                "make": "Ford",
                "model": "Focus",
                "year": 2019,
                "price": 12750,
                "mileage": 42000,
                "location": "Liverpool",
                "score": 7.8,
                "data": {
                    "id": "FF001",
                    "engine": "1.0L EcoBoost",
                    "transmission": "Manual",
                    "color": "Blue",
                    "fuel_type": "Petrol",
                    "mpg": 58,
                    "body_type": "Hatchback",
                    "reliability_score": 3.8,
                },
            },
            {
                "make": "Volkswagen",
                "model": "Golf",
                "year": 2020,
                "price": 17995,
                "mileage": 22000,
                "location": "Leeds",
                "score": 8.2,
                "data": {
                    "id": "VG001",
                    "engine": "2.0L TDI",
                    "transmission": "Automatic",
                    "color": "White",
                    "fuel_type": "Diesel",
                    "mpg": 65,
                    "body_type": "Hatchback",
                    "reliability_score": 4.2,
                },
            },
            {
                "make": "Honda",
                "model": "Civic",
                "year": 2017,
                "price": 11495,
                "mileage": 48000,
                "location": "Sheffield",
                "score": 7.5,
                "data": {
                    "id": "HC001",
                    "engine": "1.5L VTEC",
                    "transmission": "Manual",
                    "color": "Red",
                    "fuel_type": "Petrol",
                    "mpg": 55,
                    "body_type": "Hatchback",
                    "reliability_score": 4.0,
                },
            },
            {
                "make": "BMW",
                "model": "3 Series",
                "year": 2018,
                "price": 19995,
                "mileage": 32000,
                "location": "Birmingham",
                "score": 8.7,
                "data": {
                    "id": "BM001",
                    "engine": "2.0L TwinPower Turbo",
                    "transmission": "Automatic",
                    "color": "Black",
                    "fuel_type": "Diesel",
                    "mpg": 60,
                    "body_type": "Saloon",
                    "reliability_score": 3.9,
                },
            },
        ]

        # Apply the current sort and populate the table
        self._apply_sort()

        logger.info(f"Added {len(self.result_data)} test results to view")

    def _on_selection_changed(self):
        """Handle selection changes in the results table."""
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return

        # Get the row of the first selected item
        row = selected_rows[0].row()

        # Get the car data from the first cell in that row
        car_item = self.results_table.item(row, 0)
        car_data = car_item.data(Qt.ItemDataRole.UserRole)

        # Emit the signal with the car data
        logger.debug(f"Car selected: {car_data['make']} {car_data['model']}")
        self.car_selected.emit(car_data)

    def clear_results(self):
        """Clear all search results."""
        self.result_data = []
        self.filtered_data = []
        self.results_table.setRowCount(0)
        self.results_count_label.setText("0 results found")

    def add_results(self, results):
        """Add search results to the table.

        Args:
            results: List of car listing data in display format
        """
        # Store the result data
        self.result_data = results

        # Update make filter with available makes
        self._update_filter_options()

        # Apply initial filtering
        self._apply_filters()

        # Apply initial sort
        self._apply_sort()

        logger.info(f"Added {len(results)} search results to view")
