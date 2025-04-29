"""Main window for the Car Search application.

This module provides the main application window using PyQt6.
"""

import asyncio

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.logging import get_logger
from ..data.search_service import search_service
from ..models.search_parameters import SearchParameters
from .car_detail_view import CarDetailView
from .llm_config_panel import LLMConfigPanel
from .results_view import ResultsView
from .search_options_panel import SearchOptionsPanel
from .search_panel import SearchPanel

# Set up logger for this module
logger = get_logger(__name__)


class SearchThread(QThread):
    """Thread for performing car searches asynchronously."""

    search_complete = pyqtSignal(list)
    search_error = pyqtSignal(str)
    search_timeout = pyqtSignal()

    def __init__(self, search_params):
        """Initialize the search thread.

        Args:
            search_params: Search parameters dictionary
        """
        super().__init__()
        self.search_params = search_params
        # Set a maximum execution time for the search (in milliseconds)
        self.max_execution_time = 60000  # 60 seconds
        self.timer = None

    def run(self):
        """Run the search in a separate thread."""
        try:
            # Start a timer to limit the search time
            self.start_timeout_timer()

            # Create SearchParameters model
            params = SearchParameters(**self.search_params)

            # Run the async search function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(search_service.search(params))

            # Cancel the timer as we've completed successfully
            self.cancel_timeout_timer()

            # Emit result signal
            self.search_complete.emit(results)
        except Exception as e:
            logger.error(f"Error in search thread: {e}")
            self.search_error.emit(str(e))

    def start_timeout_timer(self):
        """Start a timer to limit the search execution time."""
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.handle_timeout)
        self.timer.start(self.max_execution_time)

    def cancel_timeout_timer(self):
        """Cancel the timeout timer."""
        if self.timer and self.timer.isActive():
            self.timer.stop()

    def handle_timeout(self):
        """Handle a search timeout by terminating the thread and emitting an error."""
        logger.error("Search operation timed out after 60 seconds")
        self.search_timeout.emit()
        self.terminate()  # Force terminate the thread


class MainWindow(QMainWindow):
    """Main window for the Car Search application."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        self.setWindowTitle("Car Search")
        self.resize(1000, 700)

        # Log startup
        logger.info("Initializing main window")

        # Current search thread
        self.search_thread = None

        # Progress dialog
        self.progress_dialog = None

        # Initialize UI components
        self._init_ui()

        # Show the window
        self.show()
        logger.info("Main window displayed")

    def _init_ui(self):
        """Initialize the UI components."""
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Create the main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Search parameters
        left_panel = self._create_search_panel()
        splitter.addWidget(left_panel)

        # Right panel - Results/details/LLM insights/settings
        right_panel = self._create_results_panel()
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (30% left, 70% right)
        splitter.setSizes([300, 700])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_search_panel(self):
        """Create the search parameters panel.

        Returns:
            QWidget: The search panel widget
        """
        # Create the search panel
        self.search_panel = SearchPanel()

        # Connect search signal to our search handler
        self.search_panel.search_triggered.connect(self._on_search)

        return self.search_panel

    def _create_results_panel(self):
        """Create the results and details panel.

        Returns:
            QWidget: The results panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Tabs for different views
        self.tabs = QTabWidget()

        # Results tab
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)
        results_layout.setContentsMargins(0, 0, 0, 0)

        # Add the results view
        self.results_view = ResultsView()
        self.results_view.car_selected.connect(self._on_car_selected)
        results_layout.addWidget(self.results_view)

        self.tabs.addTab(self.results_tab, "Search Results")

        # Details tab
        self.details_tab = QWidget()
        details_layout = QVBoxLayout(self.details_tab)
        details_layout.setContentsMargins(0, 0, 0, 0)

        # Add the car detail view
        self.car_detail_view = CarDetailView()
        details_layout.addWidget(self.car_detail_view)

        self.tabs.addTab(self.details_tab, "Car Details")

        # LLM Insights tab
        insights_tab = QWidget()
        insights_layout = QVBoxLayout(insights_tab)
        insights_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder for future LLM-powered insights
        insights_placeholder = QLabel("LLM-powered car insights will be shown here.")
        insights_layout.addWidget(insights_placeholder)

        self.tabs.addTab(insights_tab, "Insights")

        # LLM Config tab
        llm_config_tab = QWidget()
        llm_config_layout = QVBoxLayout(llm_config_tab)
        llm_config_layout.setContentsMargins(0, 0, 0, 0)

        # Add the LLM config panel
        self.llm_config_panel = LLMConfigPanel()
        self.llm_config_panel.config_saved.connect(self._on_llm_config_saved)
        llm_config_layout.addWidget(self.llm_config_panel)

        self.tabs.addTab(llm_config_tab, "LLM Configuration")

        # Search Options tab
        search_options_tab = QWidget()
        search_options_layout = QVBoxLayout(search_options_tab)
        search_options_layout.setContentsMargins(0, 0, 0, 0)

        # Add the search options panel
        self.search_options_panel = SearchOptionsPanel()
        self.search_options_panel.settings_saved.connect(self._on_search_options_saved)
        search_options_layout.addWidget(self.search_options_panel)

        self.tabs.addTab(search_options_tab, "Search Options")

        layout.addWidget(self.tabs)

        return panel

    def _on_search(self, search_params):
        """Handle search request from search panel.

        Args:
            search_params (dict): Dictionary containing search parameters
        """
        # Extract search parameters
        postcode = search_params["postcode"]
        radius = search_params["radius"]
        min_price = search_params["min_price"]
        max_price = search_params["max_price"]
        make = search_params["make"]
        transmission = search_params["transmission"]

        # Update status
        self.status_bar.showMessage(f"Searching for cars near {postcode}...")

        # Show progress dialog
        self.progress_dialog = QProgressDialog("Searching for cars...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("Car Search")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(500)  # Show after 500ms

        # Create and start search thread
        self.search_thread = SearchThread(search_params)
        self.search_thread.search_complete.connect(self._on_search_complete)
        self.search_thread.search_error.connect(self._on_search_error)
        self.search_thread.search_timeout.connect(self._on_search_timeout)
        self.progress_dialog.canceled.connect(self.search_thread.terminate)
        self.search_thread.start()

    def _on_car_selected(self, car_data):
        """Handle car selection from results view."""
        # Log selection
        logger.info(f"Car selected: {car_data}")

        # Update car detail view with the selected car data
        self.car_detail_view.update_car_details(car_data)

        # Switch to details tab
        self.tabs.setCurrentIndex(1)

    def _on_llm_config_saved(self, config_data):
        """Handle LLM configuration being saved.

        Args:
            config_data: Dictionary of configuration data
        """
        logger.info(f"LLM configuration updated: {config_data}")
        self.status_bar.showMessage("LLM configuration saved", 3000)

    def _on_search_options_saved(self, settings_data):
        """Handle search options being saved.

        Args:
            settings_data: Dictionary of settings data
        """
        logger.info(f"Search options updated: {settings_data}")
        self.status_bar.showMessage("Search options saved", 3000)

    def _on_search_complete(self, results):
        """Handle completed search.

        Args:
            results: List of CarListingData objects
        """
        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()

        # If no results, show a message
        if not results:
            self.status_bar.showMessage("No cars found matching your criteria")
            QMessageBox.information(self, "No Results", "No cars were found matching your search criteria.")
            return

        # Display results
        self._display_search_results(results)

        # Update status
        self.status_bar.showMessage(f"Found {len(results)} cars matching your criteria")

    def _on_search_error(self, error_message):
        """Handle search error.

        Args:
            error_message: Error message
        """
        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()

        # Display error message
        self.status_bar.showMessage(f"Error searching: {error_message}")
        QMessageBox.warning(self, "Search Error", f"An error occurred while searching: {error_message}")

    def _on_search_timeout(self):
        """Handle search timeout."""
        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()

        # Display timeout message
        self.status_bar.showMessage("Search timed out - please try with more specific criteria")
        QMessageBox.warning(
            self,
            "Search Timeout",
            "The search operation took too long to complete.\n\n"
            "This usually happens when your search criteria are too broad. "
            "Please try refining your search with more specific parameters:\n\n"
            "• Use a more specific postcode\n"
            "• Reduce the search radius\n"
            "• Narrow the price range\n"
            "• Select a specific make or model",
        )

    def _display_search_results(self, car_listings):
        """Display search results in the results view.

        Args:
            car_listings: List of CarListingData objects
        """
        # Clear existing results
        self.results_view.clear_results()

        # Convert to display format
        display_data = [listing.to_dict_for_display() for listing in car_listings]

        # Add to results view
        self.results_view.add_results(display_data)

        # Switch to results tab
        self.tabs.setCurrentIndex(0)
