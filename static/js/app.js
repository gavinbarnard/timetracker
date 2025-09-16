class TimeTracker {
    constructor() {
        this.tasks = [];
        this.currentEditingTask = null;
        this.currentView = 'list'; // 'list', 'week', 'month'
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTasks();
        this.setDefaultDates();
    }

    bindEvents() {
        // Modal events
        document.getElementById('add-task-btn').addEventListener('click', () => this.showModal());
        document.querySelector('.close').addEventListener('click', () => this.hideModal());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideModal());
        
        // Form events
        document.getElementById('task-form-element').addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // View selection events
        document.getElementById('list-view-btn').addEventListener('click', () => this.setView('list'));
        document.getElementById('week-view-btn').addEventListener('click', () => this.setView('week'));
        document.getElementById('month-view-btn').addEventListener('click', () => this.setView('month'));
        
        // Filter events
        document.getElementById('filter-btn').addEventListener('click', () => this.filterTasks());
        document.getElementById('clear-filter-btn').addEventListener('click', () => this.clearFilter());
        
        // Export events
        document.getElementById('export-btn').addEventListener('click', () => this.exportTasks());
        
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('task-form');
            if (e.target === modal) {
                this.hideModal();
            }
        });
    }

    setDefaultDates() {
        const today = new Date();
        const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
        const endOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 6));
        
        document.getElementById('start-date').value = startOfWeek.toISOString().split('T')[0];
        document.getElementById('end-date').value = endOfWeek.toISOString().split('T')[0];
    }

    async loadTasks() {
        try {
            const response = await fetch('/api/tasks');
            if (response.ok) {
                this.tasks = await response.json();
                this.renderTasks();
            } else {
                this.showError('Failed to load tasks');
            }
        } catch (error) {
            this.showError('Error loading tasks: ' + error.message);
        }
    }

    async filterTasks() {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        if (!startDate || !endDate) {
            this.showError('Please select both start and end dates');
            return;
        }
        
        try {
            const response = await fetch(`/api/tasks?start_date=${startDate}&end_date=${endDate}`);
            if (response.ok) {
                this.tasks = await response.json();
                this.renderTasks();
            } else {
                this.showError('Failed to filter tasks');
            }
        } catch (error) {
            this.showError('Error filtering tasks: ' + error.message);
        }
    }

    clearFilter() {
        this.setDefaultDates();
        this.loadTasks();
    }

    setView(viewType) {
        this.currentView = viewType;
        
        // Update active button
        document.querySelectorAll('.btn-view').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`${viewType}-view-btn`).classList.add('active');
        
        // Update container class for styling
        const container = document.getElementById('tasks-container');
        container.className = `${viewType}-view`;
        
        // Re-render tasks with new view
        this.renderTasks();
    }

    async exportTasks() {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        if (!startDate || !endDate) {
            this.showError('Please select both start and end dates for export');
            return;
        }
        
        try {
            const response = await fetch(`/api/export/csv?start_date=${startDate}&end_date=${endDate}`);
            
            if (response.ok) {
                // Create a download link
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `timetracker_export_${startDate}_to_${endDate}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showSuccess('Tasks exported successfully!');
            } else {
                const errorData = await response.json();
                this.showError('Export failed: ' + (errorData.error || 'Unknown error'));
            }
        } catch (error) {
            this.showError('Error exporting tasks: ' + error.message);
        }
    }

    renderTasks() {
        const container = document.getElementById('tasks-container');
        
        if (this.tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clock"></i>
                    <h3>No tasks found</h3>
                    <p>Start by adding your first time tracking task!</p>
                </div>
            `;
            return;
        }

        // Sort tasks chronologically by start time
        const sortedTasks = [...this.tasks].sort((a, b) => {
            return new Date(a.start_time) - new Date(b.start_time);
        });

        switch (this.currentView) {
            case 'week':
                this.renderWeekView(sortedTasks, container);
                break;
            case 'month':
                this.renderMonthView(sortedTasks, container);
                break;
            default: // 'list'
                this.renderListView(sortedTasks, container);
                break;
        }
    }

    renderListView(tasks, container) {
        container.innerHTML = tasks.map(task => this.createTaskCard(task)).join('');
    }

    renderWeekView(tasks, container) {
        const weekGroups = this.groupTasksByWeek(tasks);
        let html = '';

        for (const [weekKey, weekTasks] of Object.entries(weekGroups)) {
            const weekStart = new Date(weekKey);
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekStart.getDate() + 6);
            
            const weekTitle = `Week of ${this.formatDateShort(weekStart)} - ${this.formatDateShort(weekEnd)}`;
            
            html += `
                <div class="view-group">
                    <div class="view-group-header">
                        <h3 class="view-group-title">${weekTitle}</h3>
                    </div>
                    <div class="view-group-tasks">
                        ${weekTasks.map(task => this.createTaskCard(task)).join('')}
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    renderMonthView(tasks, container) {
        const monthGroups = this.groupTasksByMonth(tasks);
        let html = '';

        for (const [monthKey, monthTasks] of Object.entries(monthGroups)) {
            const monthDate = new Date(monthKey + '-01');
            const monthTitle = monthDate.toLocaleString('en-US', { 
                year: 'numeric', 
                month: 'long' 
            });
            
            html += `
                <div class="view-group">
                    <div class="view-group-header">
                        <h3 class="view-group-title">${monthTitle}</h3>
                    </div>
                    <div class="view-group-tasks">
                        ${monthTasks.map(task => this.createTaskCard(task)).join('')}
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    groupTasksByWeek(tasks) {
        const groups = {};
        
        tasks.forEach(task => {
            const startDate = new Date(task.start_time);
            // Get the Monday of the week
            const monday = new Date(startDate);
            monday.setDate(startDate.getDate() - (startDate.getDay() || 7) + 1);
            monday.setHours(0, 0, 0, 0);
            
            const weekKey = monday.toISOString().split('T')[0];
            
            if (!groups[weekKey]) {
                groups[weekKey] = [];
            }
            groups[weekKey].push(task);
        });

        // Sort each week's tasks chronologically
        Object.keys(groups).forEach(weekKey => {
            groups[weekKey].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        });

        return groups;
    }

    groupTasksByMonth(tasks) {
        const groups = {};
        
        tasks.forEach(task => {
            const startDate = new Date(task.start_time);
            const monthKey = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}`;
            
            if (!groups[monthKey]) {
                groups[monthKey] = [];
            }
            groups[monthKey].push(task);
        });

        // Sort each month's tasks chronologically
        Object.keys(groups).forEach(monthKey => {
            groups[monthKey].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        });

        return groups;
    }

    formatDateShort(date) {
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    }

    createTaskCard(task) {
        const startTime = new Date(task.start_time);
        const endTime = new Date(task.end_time);
        const duration = this.calculateDuration(startTime, endTime);
        
        const tickets = task.reference_tickets || [];
        const ticketsHtml = tickets.length > 0 ? `
            <div class="task-tickets">
                <div class="tickets-label">Reference Tickets:</div>
                <div class="ticket-list">
                    ${tickets.map(ticket => `<span class="ticket-tag">${ticket.trim()}</span>`).join('')}
                </div>
            </div>
        ` : '';

        return `
            <div class="task-card" data-task-id="${task.id}">
                <div class="task-header">
                    <div class="task-title">${this.escapeHtml(task.description)}</div>
                    <div class="task-actions">
                        <button class="btn btn-secondary" onclick="timeTracker.editTask('${task.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-danger" onclick="timeTracker.deleteTask('${task.id}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
                
                <div class="task-time">
                    <div class="time-item">
                        <div class="time-label">Start Time</div>
                        <div class="time-value">${this.formatDateTime(startTime)}</div>
                    </div>
                    <div class="time-item">
                        <div class="time-label">End Time</div>
                        <div class="time-value">${this.formatDateTime(endTime)}</div>
                    </div>
                </div>
                
                <div class="task-duration">
                    Duration: ${duration}
                </div>
                
                ${ticketsHtml}
            </div>
        `;
    }

    showModal(task = null) {
        const modal = document.getElementById('task-form');
        const form = document.getElementById('task-form-element');
        const title = document.getElementById('form-title');
        
        if (task) {
            // Edit mode
            this.currentEditingTask = task.id;
            title.textContent = 'Edit Task';
            document.getElementById('description').value = task.description;
            document.getElementById('start-time').value = this.formatDateTimeForInput(new Date(task.start_time));
            document.getElementById('end-time').value = this.formatDateTimeForInput(new Date(task.end_time));
            document.getElementById('reference-tickets').value = (task.reference_tickets || []).join(', ');
        } else {
            // Add mode
            this.currentEditingTask = null;
            title.textContent = 'Add New Task';
            form.reset();
            
            // Set default times (current time and one hour later)
            const now = new Date();
            const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);
            document.getElementById('start-time').value = this.formatDateTimeForInput(now);
            document.getElementById('end-time').value = this.formatDateTimeForInput(oneHourLater);
        }
        
        modal.style.display = 'block';
    }

    hideModal() {
        document.getElementById('task-form').style.display = 'none';
        this.currentEditingTask = null;
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const taskData = {
            description: formData.get('description'),
            start_time: formData.get('start_time'),
            end_time: formData.get('end_time'),
            reference_tickets: formData.get('reference_tickets')
                ? formData.get('reference_tickets').split(',').map(s => s.trim()).filter(s => s)
                : []
        };

        // Validation
        if (new Date(taskData.start_time) >= new Date(taskData.end_time)) {
            this.showError('End time must be after start time');
            return;
        }

        // Validate reference tickets are provided
        if (!taskData.reference_tickets || taskData.reference_tickets.length === 0) {
            this.showError('At least one reference ticket is required');
            return;
        }

        try {
            let response;
            if (this.currentEditingTask) {
                // Update existing task
                response = await fetch(`/api/tasks/${this.currentEditingTask}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(taskData)
                });
            } else {
                // Create new task
                response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(taskData)
                });
            }

            if (response.ok) {
                this.hideModal();
                this.loadTasks();
                this.showSuccess(this.currentEditingTask ? 'Task updated successfully' : 'Task created successfully');
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to save task');
            }
        } catch (error) {
            this.showError('Error saving task: ' + error.message);
        }
    }

    async editTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (task) {
            this.showModal(task);
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }

        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadTasks();
                this.showSuccess('Task deleted successfully');
            } else {
                this.showError('Failed to delete task');
            }
        } catch (error) {
            this.showError('Error deleting task: ' + error.message);
        }
    }

    calculateDuration(startTime, endTime) {
        const diffMs = endTime - startTime;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (diffHours === 0) {
            return `${diffMinutes}m`;
        } else if (diffMinutes === 0) {
            return `${diffHours}h`;
        } else {
            return `${diffHours}h ${diffMinutes}m`;
        }
    }

    formatDateTime(date) {
        return date.toLocaleString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatDateTimeForInput(date) {
        return date.toISOString().slice(0, 16);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: 500;
            z-index: 1001;
            max-width: 300px;
            animation: slideInRight 0.3s ease;
            ${type === 'error' ? 'background-color: #dc3545;' : 'background-color: #28a745;'}
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize the time tracker when the page loads
const timeTracker = new TimeTracker();