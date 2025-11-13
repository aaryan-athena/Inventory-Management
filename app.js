// FIFO Inventory Tracker - Main Application Logic

// State Management
let inventoryData = [];
let settings = {
    maxDiscount: 50,
    criticalDays: 3,
    warningDays: 7,
    moderateDays: 14,
    discountCritical: 50,
    discountWarning: 30,
    discountModerate: 15,
    currencySymbol: "$"
};

// Load data from localStorage on startup
function loadData() {
    const savedInventory = localStorage.getItem('inventoryData');
    const savedSettings = localStorage.getItem('settings');
    
    if (savedInventory) {
        inventoryData = JSON.parse(savedInventory);
    }
    
    if (savedSettings) {
        settings = JSON.parse(savedSettings);
    }
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('inventoryData', JSON.stringify(inventoryData));
    localStorage.setItem('settings', JSON.stringify(settings));
}

// Helper Functions
function calculateDaysUntilExpiry(expiryDateStr) {
    const expiryDate = new Date(expiryDateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    expiryDate.setHours(0, 0, 0, 0);
    const daysLeft = Math.floor((expiryDate - today) / (1000 * 60 * 60 * 24));
    return daysLeft;
}

function calculateDiscount(daysLeft) {
    if (daysLeft <= 0) {
        return { discount: settings.maxDiscount, status: "Expired" };
    } else if (daysLeft <= settings.criticalDays) {
        return { discount: settings.discountCritical, status: "Critical" };
    } else if (daysLeft <= settings.warningDays) {
        return { discount: settings.discountWarning, status: "Warning" };
    } else if (daysLeft <= settings.moderateDays) {
        return { discount: settings.discountModerate, status: "Moderate" };
    } else {
        return { discount: 0, status: "Fresh" };
    }
}

function calculateDiscountedPrice(originalPrice, discountPercent) {
    const discounted = originalPrice * (1 - discountPercent / 100);
    return discounted;
}

function formatCurrency(amount) {
    return `${settings.currencySymbol}${amount.toFixed(2)}`;
}

function getInventoryStats() {
    if (inventoryData.length === 0) {
        return {
            totalItems: 0,
            totalQuantity: 0,
            expired: 0,
            critical: 0,
            warning: 0,
            fresh: 0,
            totalValue: 0,
            potentialLoss: 0
        };
    }
    
    const stats = {
        totalItems: inventoryData.length,
        totalQuantity: 0,
        expired: 0,
        critical: 0,
        warning: 0,
        fresh: 0,
        totalValue: 0,
        potentialLoss: 0
    };
    
    inventoryData.forEach(item => {
        const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
        const { discount, status } = calculateDiscount(daysLeft);
        
        const itemValue = item.price * item.quantity;
        stats.totalQuantity += item.quantity;
        stats.totalValue += itemValue;
        
        if (status === "Expired") {
            stats.expired++;
            stats.potentialLoss += itemValue;
        } else if (status === "Critical") {
            stats.critical++;
            stats.potentialLoss += itemValue * (discount / 100);
        } else if (status === "Warning") {
            stats.warning++;
        } else {
            stats.fresh++;
        }
    });
    
    return stats;
}

// Toast Notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');
    
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const targetPage = link.getAttribute('data-page');
            
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            pages.forEach(p => p.classList.remove('active'));
            document.getElementById(`${targetPage}-page`).classList.add('active');
            
            // Refresh page content
            if (targetPage === 'home') {
                renderHomePage();
            } else if (targetPage === 'inventory') {
                renderInventoryPage();
            } else if (targetPage === 'reports') {
                renderReportsPage();
            } else if (targetPage === 'settings') {
                renderSettingsPage();
            }
        });
    });
}

// Home Page Rendering
function renderHomePage() {
    const stats = getInventoryStats();
    
    // Update metrics
    document.getElementById('total-items').textContent = stats.totalItems;
    document.getElementById('total-quantity').textContent = stats.totalQuantity;
    document.getElementById('total-value').textContent = formatCurrency(stats.totalValue);
    document.getElementById('potential-loss').textContent = formatCurrency(stats.potentialLoss);
    
    // Render status chart
    renderStatusChart(stats);
    
    // Render alerts
    renderAlerts();
    
    // Render inventory table
    renderHomeInventoryTable();
    
    // Update summary
    document.getElementById('summary-expired').textContent = stats.expired;
    document.getElementById('summary-discount').textContent = stats.critical + stats.warning;
    document.getElementById('summary-fresh').textContent = stats.fresh;
}

function renderStatusChart(stats) {
    const ctx = document.getElementById('status-chart');
    
    if (window.statusChart) {
        window.statusChart.destroy();
    }
    
    window.statusChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Fresh', 'Moderate Risk', 'Critical', 'Expired'],
            datasets: [{
                label: 'Number of Items',
                data: [stats.fresh, stats.warning, stats.critical, stats.expired],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(234, 179, 8, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgb(16, 185, 129)',
                    'rgb(234, 179, 8)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function renderAlerts() {
    const alertsContainer = document.getElementById('alerts-container');
    
    if (inventoryData.length === 0) {
        alertsContainer.innerHTML = '<div class="alert-empty">No alerts. Add inventory items to track expiry dates.</div>';
        return;
    }
    
    const alerts = [];
    
    inventoryData.forEach(item => {
        const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
        const { discount, status } = calculateDiscount(daysLeft);
        
        if (status === "Expired" || status === "Critical" || status === "Warning") {
            alerts.push({
                productName: item.productName,
                batchNumber: item.batchNumber,
                daysLeft,
                discount,
                status
            });
        }
    });
    
    alerts.sort((a, b) => a.daysLeft - b.daysLeft);
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = '<div class="alert-empty" style="color: #10b981;">✅ No critical alerts. All items are fresh!</div>';
        return;
    }
    
    const alertsHTML = alerts.slice(0, 5).map(alert => {
        const icon = alert.status === "Expired" ? "🔴" : alert.status === "Critical" ? "🟠" : "🟡";
        const className = alert.status.toLowerCase();
        const message = alert.daysLeft <= 0 
            ? `<strong>${alert.productName}</strong> (Batch #${alert.batchNumber}) – EXPIRED! Discount: ${alert.discount}%`
            : `<strong>${alert.productName}</strong> (Batch #${alert.batchNumber}) – ${alert.daysLeft} days left. Discount: ${alert.discount}%`;
        
        return `<div class="alert-item ${className}">${icon} ${message}</div>`;
    }).join('');
    
    alertsContainer.innerHTML = alertsHTML;
}

function renderHomeInventoryTable() {
    const tbody = document.querySelector('#home-inventory-table tbody');
    
    if (inventoryData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 2rem; color: #64748b;">No items in inventory yet. Go to the Inventory tab to add products.</td></tr>';
        return;
    }
    
    const rows = inventoryData.map(item => {
        const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
        const { discount, status } = calculateDiscount(daysLeft);
        const discountedPrice = calculateDiscountedPrice(item.price, discount);
        const totalValue = discountedPrice * item.quantity;
        
        return `
            <tr class="status-${status.toLowerCase()}">
                <td>${item.productName}</td>
                <td>${item.batchNumber}</td>
                <td>${item.quantity}</td>
                <td>${daysLeft}</td>
                <td><span class="status-badge ${status.toLowerCase()}">${status}</span></td>
                <td>${formatCurrency(item.price)}</td>
                <td>${discount}%</td>
                <td>${formatCurrency(discountedPrice)}</td>
                <td>${formatCurrency(totalValue)}</td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = rows;
}

// Inventory Page Rendering
function renderInventoryPage() {
    renderInventoryList();
    updateCategoryFilter();
}

function renderInventoryList() {
    const inventoryList = document.getElementById('inventory-list');
    const searchTerm = document.getElementById('search-inventory').value.toLowerCase();
    const categoryFilter = Array.from(document.getElementById('category-filter').selectedOptions).map(o => o.value);
    const statusFilter = Array.from(document.getElementById('status-filter').selectedOptions).map(o => o.value);
    
    let filteredData = inventoryData;
    
    if (searchTerm) {
        filteredData = filteredData.filter(item => 
            item.productName.toLowerCase().includes(searchTerm) ||
            item.productId.toLowerCase().includes(searchTerm) ||
            item.batchNumber.toLowerCase().includes(searchTerm)
        );
    }
    
    if (categoryFilter.length > 0 && !categoryFilter.includes('')) {
        filteredData = filteredData.filter(item => categoryFilter.includes(item.category));
    }
    
    if (statusFilter.length > 0 && !statusFilter.includes('')) {
        filteredData = filteredData.filter(item => {
            const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
            const { status } = calculateDiscount(daysLeft);
            return statusFilter.includes(status);
        });
    }
    
    if (filteredData.length === 0) {
        inventoryList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">No items found</div></div>';
        return;
    }
    
    const itemsHTML = filteredData.map((item, index) => {
        const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
        const { discount, status } = calculateDiscount(daysLeft);
        const discountedPrice = calculateDiscountedPrice(item.price, discount);
        const totalValue = discountedPrice * item.quantity;
        
        return `
            <div class="inventory-item">
                <div class="inventory-item-header">
                    <div class="inventory-item-title">${item.productName} - ${item.productId} | Status: ${status} | Discount: ${discount}%</div>
                    <span class="status-badge ${status.toLowerCase()}">${status}</span>
                </div>
                <div class="inventory-item-details">
                    <div class="inventory-item-detail"><strong>Batch:</strong> ${item.batchNumber}</div>
                    <div class="inventory-item-detail"><strong>Category:</strong> ${item.category}</div>
                    <div class="inventory-item-detail"><strong>Quantity:</strong> ${item.quantity}</div>
                    <div class="inventory-item-detail"><strong>Original Price:</strong> ${formatCurrency(item.price)}</div>
                    <div class="inventory-item-detail"><strong>Discounted Price:</strong> ${formatCurrency(discountedPrice)}</div>
                    <div class="inventory-item-detail"><strong>Total Value:</strong> ${formatCurrency(totalValue)}</div>
                    <div class="inventory-item-detail"><strong>Expiry Date:</strong> ${item.expiryDate}</div>
                    <div class="inventory-item-detail"><strong>Days Left:</strong> ${daysLeft}</div>
                    <div class="inventory-item-detail"><strong>Shelf Life:</strong> ${item.shelfLife} days</div>
                    <div class="inventory-item-detail"><strong>Location:</strong> ${item.location || 'N/A'}</div>
                    <div class="inventory-item-detail"><strong>Date Added:</strong> ${item.dateAdded}</div>
                    ${item.notes ? `<div class="inventory-item-detail"><strong>Notes:</strong> ${item.notes}</div>` : ''}
                </div>
                <div class="inventory-item-actions">
                    <button class="btn btn-danger btn-sm" onclick="deleteItem(${index})">🗑️ Delete</button>
                </div>
            </div>
        `;
    }).join('');
    
    inventoryList.innerHTML = itemsHTML;
}

function updateCategoryFilter() {
    const categoryFilter = document.getElementById('category-filter');
    const categories = [...new Set(inventoryData.map(item => item.category))];
    
    const currentSelections = Array.from(categoryFilter.selectedOptions).map(o => o.value);
    
    categoryFilter.innerHTML = '<option value="">All Categories</option>' + 
        categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');
    
    Array.from(categoryFilter.options).forEach(option => {
        if (currentSelections.includes(option.value)) {
            option.selected = true;
        }
    });
}

function deleteItem(index) {
    if (confirm('Are you sure you want to delete this item?')) {
        inventoryData.splice(index, 1);
        saveData();
        renderInventoryPage();
        showToast('Item deleted successfully', 'success');
    }
}

// Reports Page Rendering
function renderReportsPage() {
    if (inventoryData.length === 0) {
        document.getElementById('reports-page').innerHTML = `
            <div class="page-header"><h1>📊 Inventory Analytics & Reports</h1></div>
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">No inventory data available</div>
                <p>Please add items in the Inventory tab to generate reports.</p>
            </div>
        `;
        return;
    }
    
    // Calculate metrics
    let totalOriginalValue = 0;
    let totalDiscountedValue = 0;
    let totalDiscount = 0;
    let discountCount = 0;
    
    const enrichedData = inventoryData.map(item => {
        const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
        const { discount, status } = calculateDiscount(daysLeft);
        const originalTotalValue = item.price * item.quantity;
        const discountedTotalValue = calculateDiscountedPrice(item.price, discount) * item.quantity;
        const potentialLoss = originalTotalValue - discountedTotalValue;
        
        totalOriginalValue += originalTotalValue;
        totalDiscountedValue += discountedTotalValue;
        
        if (discount > 0) {
            totalDiscount += discount;
            discountCount++;
        }
        
        return {
            ...item,
            daysLeft,
            discount,
            status,
            originalTotalValue,
            discountedTotalValue,
            potentialLoss
        };
    });
    
    const avgDiscount = discountCount > 0 ? totalDiscount / discountCount : 0;
    const discountImpact = totalOriginalValue - totalDiscountedValue;
    
    // Update financial metrics
    document.getElementById('report-total-value').textContent = formatCurrency(totalOriginalValue);
    document.getElementById('report-discounted-value').textContent = formatCurrency(totalDiscountedValue);
    document.getElementById('report-discount-impact').textContent = formatCurrency(discountImpact);
    document.getElementById('report-avg-discount').textContent = `${avgDiscount.toFixed(1)}%`;
    
    // Render charts
    renderStatusReportChart();
    renderExpiryTimelineChart();
    
    // Render detailed report table
    renderReportTable(enrichedData);
    
    // Render critical items
    renderCriticalItems(enrichedData);
}

function renderStatusReportChart() {
    const ctx = document.getElementById('status-report-chart');
    
    if (window.statusReportChart) {
        window.statusReportChart.destroy();
    }
    
    const statusCounts = { Fresh: 0, Moderate: 0, Warning: 0, Critical: 0, Expired: 0 };
    
    inventoryData.forEach(item => {
        const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
        const { status } = calculateDiscount(daysLeft);
        statusCounts[status]++;
    });
    
    window.statusReportChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(statusCounts),
            datasets: [{
                data: Object.values(statusCounts),
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(234, 179, 8, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
}

function renderExpiryTimelineChart() {
    const ctx = document.getElementById('expiry-timeline-chart');
    
    if (window.expiryTimelineChart) {
        window.expiryTimelineChart.destroy();
    }
    
    const bins = {
        'Expired': 0,
        '0-3 days': 0,
        '4-7 days': 0,
        '8-14 days': 0,
        '15-30 days': 0,
        '30+ days': 0
    };
    
    inventoryData.forEach(item => {
        const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
        
        if (daysLeft <= 0) bins['Expired']++;
        else if (daysLeft <= 3) bins['0-3 days']++;
        else if (daysLeft <= 7) bins['4-7 days']++;
        else if (daysLeft <= 14) bins['8-14 days']++;
        else if (daysLeft <= 30) bins['15-30 days']++;
        else bins['30+ days']++;
    });
    
    window.expiryTimelineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(bins),
            datasets: [{
                label: 'Number of Items',
                data: Object.values(bins),
                backgroundColor: 'rgba(79, 70, 229, 0.8)',
                borderColor: 'rgb(79, 70, 229)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function renderReportTable(enrichedData) {
    const tbody = document.querySelector('#report-table tbody');
    const sortBy = document.getElementById('sort-by').value;
    const sortOrder = document.getElementById('sort-order').value;
    
    const sortedData = [...enrichedData].sort((a, b) => {
        let aVal, bVal;
        
        switch(sortBy) {
            case 'daysUntilExpiry':
                aVal = a.daysLeft;
                bVal = b.daysLeft;
                break;
            case 'discount':
                aVal = a.discount;
                bVal = b.discount;
                break;
            case 'status':
                aVal = a.status;
                bVal = b.status;
                break;
            case 'productName':
                aVal = a.productName;
                bVal = b.productName;
                break;
            case 'potentialLoss':
                aVal = a.potentialLoss;
                bVal = b.potentialLoss;
                break;
            default:
                aVal = a.daysLeft;
                bVal = b.daysLeft;
        }
        
        if (sortOrder === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });
    
    const rows = sortedData.map(item => `
        <tr class="status-${item.status.toLowerCase()}">
            <td>${item.productName}</td>
            <td>${item.productId}</td>
            <td>${item.batchNumber}</td>
            <td>${item.category}</td>
            <td>${item.quantity}</td>
            <td>${item.expiryDate}</td>
            <td>${item.daysLeft}</td>
            <td><span class="status-badge ${item.status.toLowerCase()}">${item.status}</span></td>
            <td>${item.discount}%</td>
            <td>${formatCurrency(item.price)}</td>
            <td>${formatCurrency(item.originalTotalValue)}</td>
            <td>${formatCurrency(item.discountedTotalValue)}</td>
            <td>${formatCurrency(item.potentialLoss)}</td>
        </tr>
    `).join('');
    
    tbody.innerHTML = rows;
}

function renderCriticalItems(enrichedData) {
    const criticalItemsList = document.getElementById('critical-items-list');
    const criticalItems = enrichedData.filter(item => item.status === 'Expired' || item.status === 'Critical');
    
    if (criticalItems.length === 0) {
        criticalItemsList.innerHTML = '<div class="alert-empty" style="color: #10b981;">✅ No critical items. All inventory is in good condition!</div>';
        return;
    }
    
    const itemsHTML = criticalItems.map(item => {
        const actions = item.daysLeft <= 0 
            ? `<li>Remove from inventory immediately</li><li>Dispose according to regulations</li>`
            : `<li>Apply ${item.discount}% discount</li><li>Promote with special signage</li><li>Consider bundling with popular items</li>`;
        
        return `
            <div class="critical-item">
                <div class="critical-item-header">🔴 ${item.productName} - ${item.status}</div>
                <div class="critical-item-details">
                    <div><strong>Product ID:</strong> ${item.productId}</div>
                    <div><strong>Batch:</strong> ${item.batchNumber}</div>
                    <div><strong>Days Left:</strong> ${item.daysLeft}</div>
                    <div><strong>Quantity:</strong> ${item.quantity}</div>
                    <div><strong>Current Discount:</strong> ${item.discount}%</div>
                    <div><strong>Potential Loss:</strong> ${formatCurrency(item.potentialLoss)}</div>
                </div>
                <div class="critical-item-actions">
                    <strong>Recommended Actions:</strong>
                    <ul>${actions}</ul>
                </div>
            </div>
        `;
    }).join('');
    
    criticalItemsList.innerHTML = `<div style="color: #ef4444; margin-bottom: 1rem;">⚠️ ${criticalItems.length} items require immediate attention!</div>` + itemsHTML;
}

// Settings Page Rendering
function renderSettingsPage() {
    document.getElementById('critical-days').value = settings.criticalDays;
    document.getElementById('warning-days').value = settings.warningDays;
    document.getElementById('moderate-days').value = settings.moderateDays;
    document.getElementById('discount-critical').value = settings.discountCritical;
    document.getElementById('discount-warning').value = settings.discountWarning;
    document.getElementById('discount-moderate').value = settings.discountModerate;
    document.getElementById('max-discount').value = settings.maxDiscount;
    
    document.getElementById('discount-critical-value').textContent = `${settings.discountCritical}%`;
    document.getElementById('discount-warning-value').textContent = `${settings.discountWarning}%`;
    document.getElementById('discount-moderate-value').textContent = `${settings.discountModerate}%`;
    document.getElementById('max-discount-value').textContent = `${settings.maxDiscount}%`;
}

// Form Handling
function initInventoryForm() {
    const form = document.getElementById('inventory-form');
    const expiryDateInput = document.getElementById('expiry-date');
    
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    expiryDateInput.min = today;
    expiryDateInput.value = today;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const productName = document.getElementById('product-name').value;
        const productId = document.getElementById('product-id').value;
        const batchNumber = document.getElementById('batch-number').value;
        const expiryDate = document.getElementById('expiry-date').value;
        const quantity = parseInt(document.getElementById('quantity').value);
        const price = parseFloat(document.getElementById('price').value);
        const shelfLife = parseInt(document.getElementById('shelf-life').value);
        const category = document.getElementById('category').value;
        const location = document.getElementById('location').value;
        const notes = document.getElementById('notes').value;
        
        // Check for duplicate Product ID
        if (inventoryData.some(item => item.productId === productId)) {
            showToast(`Product ID '${productId}' already exists. Please use a unique ID.`, 'error');
            return;
        }
        
        const newItem = {
            productName,
            productId,
            batchNumber,
            expiryDate,
            quantity,
            price,
            shelfLife,
            category,
            location,
            notes,
            dateAdded: new Date().toISOString().split('T')[0]
        };
        
        inventoryData.push(newItem);
        saveData();
        form.reset();
        expiryDateInput.value = today;
        renderInventoryPage();
        showToast(`${productName} (ID: ${productId}) successfully added to inventory!`, 'success');
    });
}

// Settings Event Handlers
function initSettings() {
    // Update slider values
    ['discount-critical', 'discount-warning', 'discount-moderate', 'max-discount'].forEach(id => {
        const slider = document.getElementById(id);
        const valueSpan = document.getElementById(`${id}-value`);
        
        slider.addEventListener('input', () => {
            valueSpan.textContent = `${slider.value}%`;
        });
    });
    
    // Save settings
    document.getElementById('save-settings').addEventListener('click', () => {
        settings.criticalDays = parseInt(document.getElementById('critical-days').value);
        settings.warningDays = parseInt(document.getElementById('warning-days').value);
        settings.moderateDays = parseInt(document.getElementById('moderate-days').value);
        settings.discountCritical = parseInt(document.getElementById('discount-critical').value);
        settings.discountWarning = parseInt(document.getElementById('discount-warning').value);
        settings.discountModerate = parseInt(document.getElementById('discount-moderate').value);
        settings.maxDiscount = parseInt(document.getElementById('max-discount').value);
        
        saveData();
        showToast('Settings saved successfully!', 'success');
    });
    
    // Reset settings
    document.getElementById('reset-settings').addEventListener('click', () => {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            settings = {
                maxDiscount: 50,
                criticalDays: 3,
                warningDays: 7,
                moderateDays: 14,
                discountCritical: 50,
                discountWarning: 30,
                discountModerate: 15,
                currencySymbol: "$"
            };
            saveData();
            renderSettingsPage();
            showToast('Settings reset to defaults!', 'success');
        }
    });
}

// Data Management
function initDataManagement() {
    // Export all data
    document.getElementById('export-all-data').addEventListener('click', () => {
        const data = {
            inventory: inventoryData,
            settings: settings,
            exportDate: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `inventory_backup_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        showToast('Data exported successfully!', 'success');
    });
    
    // Import data
    document.getElementById('import-data-btn').addEventListener('click', () => {
        document.getElementById('import-file').click();
    });
    
    document.getElementById('import-file').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                
                if (data.inventory) {
                    inventoryData = data.inventory;
                }
                if (data.settings) {
                    settings = data.settings;
                }
                
                saveData();
                showToast('Data imported successfully!', 'success');
                renderHomePage();
            } catch (error) {
                showToast('Error importing file: Invalid format', 'error');
            }
        };
        reader.readAsText(file);
    });
    
    // Clear inventory data
    document.getElementById('clear-inventory-data').addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all inventory data? This action cannot be undone!')) {
            inventoryData = [];
            saveData();
            showToast('All inventory data cleared!', 'success');
            renderHomePage();
        }
    });
    
    // Reset everything
    document.getElementById('reset-everything').addEventListener('click', () => {
        if (confirm('Are you sure you want to reset everything? This will clear all data and settings!')) {
            inventoryData = [];
            settings = {
                maxDiscount: 50,
                criticalDays: 3,
                warningDays: 7,
                moderateDays: 14,
                discountCritical: 50,
                discountWarning: 30,
                discountModerate: 15,
                currencySymbol: "$"
            };
            saveData();
            showToast('System reset complete!', 'success');
            renderHomePage();
            renderSettingsPage();
        }
    });
}

// Export Functions
function initExportFunctions() {
    // Export CSV from inventory page
    document.getElementById('export-csv').addEventListener('click', () => {
        if (inventoryData.length === 0) {
            showToast('No data to export', 'warning');
            return;
        }
        
        const csv = generateInventoryCSV(inventoryData);
        downloadCSV(csv, `inventory_${new Date().toISOString().split('T')[0]}.csv`);
        showToast('Inventory exported successfully!', 'success');
    });
    
    // Clear all inventory
    document.getElementById('clear-all').addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all inventory? This action cannot be undone!')) {
            inventoryData = [];
            saveData();
            renderInventoryPage();
            showToast('All inventory cleared!', 'success');
        }
    });
    
    // Export full report
    document.getElementById('export-full-report').addEventListener('click', () => {
        if (inventoryData.length === 0) {
            showToast('No data to export', 'warning');
            return;
        }
        
        const enrichedData = inventoryData.map(item => {
            const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
            const { discount, status } = calculateDiscount(daysLeft);
            return { ...item, daysLeft, discount, status };
        });
        
        const csv = generateReportCSV(enrichedData);
        downloadCSV(csv, `inventory_report_${new Date().toISOString().split('T')[0]}.csv`);
        showToast('Full report exported!', 'success');
    });
    
    // Export critical items
    document.getElementById('export-critical').addEventListener('click', () => {
        const criticalItems = inventoryData.filter(item => {
            const daysLeft = calculateDaysUntilExpiry(item.expiryDate);
            const { status } = calculateDiscount(daysLeft);
            return status === 'Expired' || status === 'Critical';
        });
        
        if (criticalItems.length === 0) {
            showToast('No critical items to export', 'warning');
            return;
        }
        
        const csv = generateInventoryCSV(criticalItems);
        downloadCSV(csv, `critical_items_${new Date().toISOString().split('T')[0]}.csv`);
        showToast('Critical items exported!', 'success');
    });
    
    // Export summary
    document.getElementById('export-summary').addEventListener('click', () => {
        if (inventoryData.length === 0) {
            showToast('No data to export', 'warning');
            return;
        }
        
        const stats = getInventoryStats();
        const csv = `Metric,Value\nTotal Items,${stats.totalItems}\nTotal Value,$${stats.totalValue.toFixed(2)}\nExpired Items,${stats.expired}\nCritical Items,${stats.critical}`;
        downloadCSV(csv, `summary_${new Date().toISOString().split('T')[0]}.csv`);
        showToast('Summary exported!', 'success');
    });
}

function generateInventoryCSV(data) {
    const headers = ['Product Name', 'Product ID', 'Batch Number', 'Category', 'Quantity', 'Price', 'Expiry Date', 'Shelf Life', 'Location', 'Notes', 'Date Added'];
    const rows = data.map(item => [
        item.productName,
        item.productId,
        item.batchNumber,
        item.category,
        item.quantity,
        item.price,
        item.expiryDate,
        item.shelfLife,
        item.location || '',
        item.notes || '',
        item.dateAdded
    ]);
    
    return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
}

function generateReportCSV(data) {
    const headers = ['Product Name', 'Product ID', 'Batch Number', 'Category', 'Quantity', 'Expiry Date', 'Days Until Expiry', 'Status', 'Discount %', 'Price'];
    const rows = data.map(item => [
        item.productName,
        item.productId,
        item.batchNumber,
        item.category,
        item.quantity,
        item.expiryDate,
        item.daysLeft,
        item.status,
        item.discount,
        item.price
    ]);
    
    return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// Search and Filter Event Handlers
function initSearchAndFilters() {
    document.getElementById('search-inventory').addEventListener('input', renderInventoryList);
    document.getElementById('category-filter').addEventListener('change', renderInventoryList);
    document.getElementById('status-filter').addEventListener('change', renderInventoryList);
    document.getElementById('sort-by').addEventListener('change', () => renderReportsPage());
    document.getElementById('sort-order').addEventListener('change', () => renderReportsPage());
}

// Initialize Application
function init() {
    loadData();
    initNavigation();
    initInventoryForm();
    initSettings();
    initDataManagement();
    initExportFunctions();
    initSearchAndFilters();
    renderHomePage();
}

// Run on page load
document.addEventListener('DOMContentLoaded', init);
