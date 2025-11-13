# FIFO Inventory Tracker

A modern, responsive web application for managing inventory with automatic discount calculations based on expiry dates.

## Features

- **Real-time Inventory Tracking**: Add, view, and manage inventory items with expiry dates
- **Automatic Discount Calculation**: Dynamic pricing based on days until expiry
- **Comprehensive Dashboard**: Visual analytics with charts and metrics
- **Advanced Filtering**: Search and filter by category, status, and more
- **Detailed Reports**: Generate comprehensive inventory reports
- **Data Management**: Export/import data in JSON and CSV formats
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Local Storage**: All data persists in your browser

## Getting Started

### Installation

1. Clone or download this repository
2. Open `index.html` in a modern web browser (Chrome, Firefox, Safari, or Edge)

That's it! No server or installation required.

### Usage

#### Adding Inventory Items

1. Navigate to the **Inventory** tab
2. Fill in the product details in the form
3. Click "Add Item" to save

#### Viewing Dashboard

The **Home** tab displays:
- Key metrics (total items, quantity, value, potential loss)
- Inventory status chart
- Priority alerts for expiring items
- Current inventory table with live pricing

#### Generating Reports

The **Reports** tab provides:
- Financial overview
- Status and expiry timeline charts
- Detailed inventory report
- Critical action items
- Export options (CSV)

#### Configuring Settings

The **Settings** tab allows you to:
- Adjust expiry thresholds
- Configure discount percentages
- Export/import data
- Reset system

## Discount Algorithm

The system automatically calculates discounts based on days until expiry:

- **Expired** (≤ 0 days): 50% discount (default)
- **Critical** (1-3 days): 50% discount (default)
- **Warning** (4-7 days): 30% discount (default)
- **Moderate** (8-14 days): 15% discount (default)
- **Fresh** (> 14 days): No discount

All thresholds and percentages are customizable in Settings.

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Data Storage

All data is stored locally in your browser using localStorage. Your data:
- Persists between sessions
- Is private to your browser
- Can be exported as JSON backup
- Is not sent to any server

## Technologies Used

- HTML5
- CSS3 (Modern Flexbox & Grid)
- Vanilla JavaScript (ES6+)
- Chart.js for data visualization
- LocalStorage API for data persistence

## File Structure

```
├── index.html      # Main HTML structure
├── styles.css      # All styling and responsive design
├── app.js          # Application logic and functionality
└── README.md       # Documentation
```

## Customization

### Changing Colors

Edit the CSS variables in `styles.css`:

```css
:root {
    --primary-color: #4f46e5;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
    /* ... more variables */
}
```

### Modifying Discount Logic

Edit the `calculateDiscount()` function in `app.js` to implement custom discount rules.

## Tips

- **Regular Backups**: Export your data regularly using the Settings page
- **Mobile Access**: Add to home screen on mobile for app-like experience
- **Keyboard Shortcuts**: Use Tab to navigate forms quickly
- **Bulk Operations**: Use CSV export/import for bulk data management

## Support

For issues or questions, please refer to the code comments or modify as needed for your specific use case.

## License

Free to use and modify for personal or commercial projects.
