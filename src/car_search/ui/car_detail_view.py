"""Car detail view for the Car Search application.

This module provides a view for displaying detailed information about a selected car.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core.logging import get_logger

# Set up logger for this module
logger = get_logger(__name__)


class CarDetailView(QWidget):
    """View for displaying detailed information about a selected car."""

    def __init__(self):
        """Initialize the car detail view."""
        super().__init__()

        # Log initialization
        logger.info("Initializing car detail view")

        # Currently displayed car data
        self.current_car = None

        # Initialize UI components
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        # Create a scroll area to contain all details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # Create a widget to hold all the detail content
        content_widget = QWidget()
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)

        # Initial empty state
        self.empty_label = QLabel("Select a car to see details")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #666; font-size: 14px;")
        self.main_layout.addWidget(self.empty_label)

        # Car header section (initially hidden)
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)

        # Car image placeholder
        self.car_image = QLabel()
        self.car_image.setFixedSize(300, 200)
        self.car_image.setStyleSheet("background-color: #eee; border-radius: 5px;")
        self.car_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.car_image.setText("No Image Available")
        header_layout.addWidget(self.car_image)

        # Car title and price info
        title_price_layout = QVBoxLayout()

        # Car title
        self.car_title = QLabel()
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.car_title.setFont(title_font)
        title_price_layout.addWidget(self.car_title)

        # Car subtitle (year, mileage)
        self.car_subtitle = QLabel()
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        self.car_subtitle.setFont(subtitle_font)
        self.car_subtitle.setStyleSheet("color: #555;")
        title_price_layout.addWidget(self.car_subtitle)

        # Spacer
        title_price_layout.addStretch(1)

        # Price
        self.car_price = QLabel()
        price_font = QFont()
        price_font.setPointSize(14)
        price_font.setBold(True)
        self.car_price.setFont(price_font)
        self.car_price.setStyleSheet("color: #2e7d32;")  # Green color for price
        title_price_layout.addWidget(self.car_price)

        # Add title/price layout to header
        header_layout.addLayout(title_price_layout, 1)

        # Add header to main layout (initially hidden)
        self.header_widget.setVisible(False)
        self.main_layout.addWidget(self.header_widget)

        # Key specs section
        self.specs_widget = QWidget()
        specs_layout = QGridLayout(self.specs_widget)
        specs_layout.setColumnStretch(1, 1)  # Make the second column stretch
        specs_layout.setColumnStretch(3, 1)  # Make the fourth column stretch

        # Create spec labels
        self.create_spec_label("Engine:", specs_layout, 0, 0)
        self.engine_value = self.create_value_label(specs_layout, 0, 1)

        self.create_spec_label("Transmission:", specs_layout, 0, 2)
        self.transmission_value = self.create_value_label(specs_layout, 0, 3)

        self.create_spec_label("Fuel Type:", specs_layout, 1, 0)
        self.fuel_type_value = self.create_value_label(specs_layout, 1, 1)

        self.create_spec_label("MPG:", specs_layout, 1, 2)
        self.mpg_value = self.create_value_label(specs_layout, 1, 3)

        self.create_spec_label("Body Type:", specs_layout, 2, 0)
        self.body_type_value = self.create_value_label(specs_layout, 2, 1)

        self.create_spec_label("Color:", specs_layout, 2, 2)
        self.color_value = self.create_value_label(specs_layout, 2, 3)

        # Add specs to main layout (initially hidden)
        self.specs_widget.setVisible(False)
        self.main_layout.addWidget(self.specs_widget)

        # Ratings section
        self.ratings_widget = QWidget()
        ratings_layout = QGridLayout(self.ratings_widget)

        # Reliability rating
        self.create_rating_label("Reliability Rating", ratings_layout, 0, 0)
        self.reliability_stars = self.create_stars_widget()
        ratings_layout.addWidget(self.reliability_stars, 0, 1)

        # Safety rating (if available)
        self.create_rating_label("Safety Rating", ratings_layout, 1, 0)
        self.safety_stars = self.create_stars_widget()
        ratings_layout.addWidget(self.safety_stars, 1, 1)

        # Owner satisfaction (if available)
        self.create_rating_label("Owner Satisfaction", ratings_layout, 2, 0)
        self.satisfaction_stars = self.create_stars_widget()
        ratings_layout.addWidget(self.satisfaction_stars, 2, 1)

        # Add ratings to main layout (initially hidden)
        self.ratings_widget.setVisible(False)
        self.main_layout.addWidget(self.ratings_widget)

        # Pros and cons section (initially hidden)
        self.pros_cons_widget = QWidget()
        pros_cons_layout = QHBoxLayout(self.pros_cons_widget)

        # Pros
        pros_layout = QVBoxLayout()
        pros_title = QLabel("Pros")
        pros_title.setStyleSheet("font-weight: bold; color: #2e7d32;")
        pros_layout.addWidget(pros_title)
        self.pros_list = QLabel("• None listed")
        self.pros_list.setWordWrap(True)
        pros_layout.addWidget(self.pros_list)
        pros_layout.addStretch(1)
        pros_cons_layout.addLayout(pros_layout, 1)

        # Cons
        cons_layout = QVBoxLayout()
        cons_title = QLabel("Cons")
        cons_title.setStyleSheet("font-weight: bold; color: #c62828;")
        cons_layout.addWidget(cons_title)
        self.cons_list = QLabel("• None listed")
        self.cons_list.setWordWrap(True)
        cons_layout.addWidget(self.cons_list)
        cons_layout.addStretch(1)
        pros_cons_layout.addLayout(cons_layout, 1)

        # Add pros/cons to main layout (initially hidden)
        self.pros_cons_widget.setVisible(False)
        self.main_layout.addWidget(self.pros_cons_widget)

        # Set scroll area's widget
        scroll_area.setWidget(content_widget)

        # Add scroll area to this widget's layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)

    def create_spec_label(self, text, layout, row, col):
        """Create a specification label."""
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(label, row, col)
        return label

    def create_value_label(self, layout, row, col):
        """Create a value label for specifications."""
        label = QLabel()
        layout.addWidget(label, row, col)
        return label

    def create_rating_label(self, text, layout, row, col):
        """Create a rating label."""
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(label, row, col)
        return label

    def create_stars_widget(self):
        """Create a widget to display star ratings."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Create five star labels
        self.stars = []
        for _ in range(5):
            star = QLabel()
            star.setFixedSize(20, 20)
            layout.addWidget(star)
            self.stars.append(star)

        layout.addStretch(1)
        return widget

    def set_star_rating(self, stars_widget, rating):
        """Set a star rating value by highlighting the appropriate number of stars."""
        stars = stars_widget.findChildren(QLabel)

        # Handle None value
        if rating is None:
            rating = 0

        # Validate rating
        rating = max(0, min(5, rating))

        # Calculate full and partial stars
        full_stars = int(rating)
        partial = rating - full_stars

        # Set star images based on rating
        for i, star in enumerate(stars):
            if i < full_stars:
                star.setStyleSheet("background-color: gold; border-radius: 10px;")
            elif i == full_stars and partial > 0:
                # Create a partially filled star using a background gradient
                if partial >= 0.75:
                    color = "qlineargradient(x1:0, x2:1, y1:0, y2:0, stop:0.75 gold, stop:0.751 lightgray)"
                elif partial >= 0.5:
                    color = "qlineargradient(x1:0, x2:1, y1:0, y2:0, stop:0.5 gold, stop:0.501 lightgray)"
                elif partial >= 0.25:
                    color = "qlineargradient(x1:0, x2:1, y1:0, y2:0, stop:0.25 gold, stop:0.251 lightgray)"
                else:
                    color = "lightgray"

                star.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
            else:
                star.setStyleSheet("background-color: lightgray; border-radius: 10px;")

    def update_car_details(self, car_data):
        """Update the view with details of the selected car.

        Args:
            car_data: Dictionary containing car details
        """
        # Store the current car data
        self.current_car = car_data

        if not car_data:
            # Show empty state
            self.empty_label.setVisible(True)
            self.header_widget.setVisible(False)
            self.specs_widget.setVisible(False)
            self.ratings_widget.setVisible(False)
            self.pros_cons_widget.setVisible(False)
            return

        # Hide empty state, show details
        self.empty_label.setVisible(False)
        self.header_widget.setVisible(True)
        self.specs_widget.setVisible(True)
        self.ratings_widget.setVisible(True)

        # Update header information
        make = car_data.get("make", "")
        model = car_data.get("model", "")
        self.car_title.setText(f"{make} {model}")

        year = car_data.get("year", "")
        mileage = car_data.get("mileage", 0)
        mileage_formatted = f"{mileage:,} miles" if mileage else "Mileage unknown"
        self.car_subtitle.setText(f"{year} • {mileage_formatted}")

        price = car_data.get("price", 0)
        self.car_price.setText(f"£{price:,}")

        # Get detailed data
        details = car_data.get("data", {})

        # Update specs
        self.engine_value.setText(details.get("engine", "Not specified"))
        self.transmission_value.setText(details.get("transmission", "Not specified"))
        self.fuel_type_value.setText(details.get("fuel_type", "Not specified"))

        # Format MPG if available
        mpg = details.get("mpg")
        if mpg:
            self.mpg_value.setText(f"{mpg} mpg")
        else:
            self.mpg_value.setText("Not specified")

        self.body_type_value.setText(details.get("body_type", "Not specified"))
        self.color_value.setText(details.get("color", "Not specified"))

        # Update ratings
        reliability_score = details.get("reliability_score", 0)
        self.set_star_rating(self.reliability_stars, reliability_score)

        # Update safety rating if available
        safety_score = details.get("safety_score", 0)
        self.set_star_rating(self.safety_stars, safety_score)

        # Update owner satisfaction if available
        satisfaction_score = details.get("owner_satisfaction", 0)
        self.set_star_rating(self.satisfaction_stars, satisfaction_score)

        # Update pros and cons if available
        pros = details.get("pros", [])
        cons = details.get("cons", [])

        if pros or cons:
            self.pros_cons_widget.setVisible(True)

            # Format pros list
            if pros:
                pros_text = "\n".join(f"• {pro}" for pro in pros)
                self.pros_list.setText(pros_text)
            else:
                self.pros_list.setText("• None listed")

            # Format cons list
            if cons:
                cons_text = "\n".join(f"• {con}" for con in cons)
                self.cons_list.setText(cons_text)
            else:
                self.cons_list.setText("• None listed")
        else:
            self.pros_cons_widget.setVisible(False)

        logger.info(f"Updated car details for {make} {model}")

    def add_test_data(self):
        """Add test data to the view."""
        test_car = {
            "make": "Toyota",
            "model": "Corolla",
            "year": 2018,
            "price": 14995,
            "mileage": 35000,
            "data": {
                "id": "TC001",
                "engine": "1.8L Hybrid",
                "transmission": "Automatic",
                "color": "Silver",
                "fuel_type": "Hybrid",
                "mpg": 62,
                "body_type": "Hatchback",
                "reliability_score": 4.5,
                "safety_score": 4.2,
                "owner_satisfaction": 3.8,
                "pros": ["Excellent fuel economy", "Strong reliability history", "Good standard safety features"],
                "cons": ["Bland driving experience", "Limited rear legroom", "Small trunk space"],
            },
        }

        self.update_car_details(test_car)
        logger.info("Added test data to car detail view")
