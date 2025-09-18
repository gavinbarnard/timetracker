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
        
        // Validate required dates based on view type
        if (this.currentView === 'list') {
            if (!startDate || !endDate) {
                this.showError('Please select both start and end dates');
                return;
            }
        } else {
            if (!startDate) {
                this.showError('Please select a start date');
                return;
            }
        }
        
        try {
            let response;
            if (this.currentView === 'list') {
                // List view uses both dates
                response = await fetch(`/api/tasks?start_date=${startDate}&end_date=${endDate}`);
            } else {
                // Week and month views only use start date, but we'll fetch all tasks and filter client-side
                response = await fetch('/api/tasks');
            }
            
            if (response.ok) {
                let tasks = await response.json();
                
                // For week and month views, filter tasks based on the specific view logic
                if (this.currentView === 'week') {
                    tasks = this.filterTasksForWeekView(tasks, startDate);
                } else if (this.currentView === 'month') {
                    tasks = this.filterTasksForMonthView(tasks, startDate);
                }
                
                this.tasks = tasks;
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

    filterTasksForWeekView(tasks, startDate) {
        const weekStart = new Date(startDate);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);
        
        return tasks.filter(task => {
            const taskDate = new Date(task.start_time);
            taskDate.setHours(0, 0, 0, 0);
            weekStart.setHours(0, 0, 0, 0);
            weekEnd.setHours(23, 59, 59, 999);
            
            return taskDate >= weekStart && taskDate <= weekEnd;
        });
    }

    filterTasksForMonthView(tasks, startDate) {
        const selectedDate = new Date(startDate);
        const monthStart = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
        const monthEnd = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);
        
        return tasks.filter(task => {
            const taskDate = new Date(task.start_time);
            taskDate.setHours(0, 0, 0, 0);
            monthStart.setHours(0, 0, 0, 0);
            monthEnd.setHours(23, 59, 59, 999);
            
            return taskDate >= monthStart && taskDate <= monthEnd;
        });
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
        const startDate = document.getElementById('start-date').value;
        if (!startDate) {
            container.innerHTML = '<div class="empty-state"><p>Please select a start date to view the week</p></div>';
            return;
        }

        const weekStart = new Date(startDate);
        weekStart.setHours(0, 0, 0, 0);

        // Group tasks by day
        const dayGroups = {};
        
        // Initialize all 7 days
        for (let i = 0; i < 7; i++) {
            const currentDay = new Date(weekStart);
            currentDay.setDate(weekStart.getDate() + i);
            const dayKey = currentDay.toISOString().split('T')[0];
            dayGroups[dayKey] = [];
        }

        // Add tasks to appropriate days
        tasks.forEach(task => {
            const taskDate = new Date(task.start_time);
            const dayKey = taskDate.toISOString().split('T')[0];
            if (dayGroups[dayKey]) {
                dayGroups[dayKey].push(task);
            }
        });

        // Sort tasks within each day chronologically
        Object.keys(dayGroups).forEach(dayKey => {
            dayGroups[dayKey].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        });

        // Create the 7-day layout
        let html = '<div class="week-grid">';
        
        for (let i = 0; i < 7; i++) {
            const currentDay = new Date(weekStart);
            currentDay.setDate(weekStart.getDate() + i);
            const dayKey = currentDay.toISOString().split('T')[0];
            const dayTasks = dayGroups[dayKey] || [];
            
            const dayName = currentDay.toLocaleDateString('en-US', { weekday: 'short' });
            const dayNumber = currentDay.getDate();
            
            html += `
                <div class="week-day">
                    <div class="week-day-header">
                        <div class="day-name">${dayName}</div>
                        <div class="day-number">${dayNumber}</div>
                    </div>
                    <div class="week-day-tasks">
                        ${dayTasks.map(task => this.createWeekTaskCard(task)).join('')}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }

    renderMonthView(tasks, container) {
        const startDate = document.getElementById('start-date').value;
        if (!startDate) {
            container.innerHTML = '<div class="empty-state"><p>Please select a start date to view the month</p></div>';
            return;
        }

        const selectedDate = new Date(startDate);
        const year = selectedDate.getFullYear();
        const month = selectedDate.getMonth();
        
        const monthStart = new Date(year, month, 1);
        const monthEnd = new Date(year, month + 1, 0);
        const daysInMonth = monthEnd.getDate();
        
        // Get the first day of the week (0 = Sunday, 1 = Monday, etc.)
        const firstDayOfWeek = monthStart.getDay();
        
        // Group tasks by day
        const dayGroups = {};
        
        // Initialize all days in the month
        for (let day = 1; day <= daysInMonth; day++) {
            const currentDay = new Date(year, month, day);
            const dayKey = currentDay.toISOString().split('T')[0];
            dayGroups[dayKey] = [];
        }

        // Add tasks to appropriate days
        tasks.forEach(task => {
            const taskDate = new Date(task.start_time);
            const dayKey = taskDate.toISOString().split('T')[0];
            if (dayGroups[dayKey]) {
                dayGroups[dayKey].push(task);
            }
        });

        // Sort tasks within each day chronologically
        Object.keys(dayGroups).forEach(dayKey => {
            dayGroups[dayKey].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        });

        const monthTitle = selectedDate.toLocaleString('en-US', { 
            year: 'numeric', 
            month: 'long' 
        });

        // Create calendar grid
        let html = `
            <div class="month-calendar">
                <div class="month-header">
                    <h3>${monthTitle}</h3>
                </div>
                <div class="calendar-grid">
                    <div class="calendar-weekdays">
                        <div class="weekday">M</div>
                        <div class="weekday">T</div>
                        <div class="weekday">W</div>
                        <div class="weekday">Th</div>
                        <div class="weekday">F</div>
                        <div class="weekday">S</div>
                        <div class="weekday">Su</div>
                    </div>
                    <div class="calendar-days">
        `;

        // Add empty cells for days before the first day of the month
        // Adjust for Monday start (0 = Sunday, 1 = Monday)
        const mondayFirstDay = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;
        for (let i = 0; i < mondayFirstDay; i++) {
            html += '<div class="calendar-day empty"></div>';
        }

        // Add all days in the month
        for (let day = 1; day <= daysInMonth; day++) {
            const currentDay = new Date(year, month, day);
            const dayKey = currentDay.toISOString().split('T')[0];
            const dayTasks = dayGroups[dayKey] || [];
            
            html += `
                <div class="calendar-day">
                    <div class="day-number">${day}</div>
                    <div class="day-tasks">
                        ${dayTasks.map(task => this.createMonthTaskCard(task)).join('')}
                    </div>
                </div>
            `;
        }

        html += `
                    </div>
                </div>
            </div>
        `;
        
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

    createWeekTaskCard(task) {
        const startTime = new Date(task.start_time);
        const endTime = new Date(task.end_time);
        const duration = this.calculateDuration(startTime, endTime);
        
        const timeStr = startTime.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit', 
            hour12: false 
        });

        return `
            <div class="week-task-card" data-task-id="${task.id}" onclick="timeTracker.editTask('${task.id}')">
                <div class="week-task-time">${timeStr}</div>
                <div class="week-task-description">${this.escapeHtml(task.description)}</div>
                <div class="week-task-duration">${duration}</div>
            </div>
        `;
    }

    createMonthTaskCard(task) {
        const startTime = new Date(task.start_time);
        const timeStr = startTime.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit', 
            hour12: false 
        });

        return `
            <div class="month-task-card" data-task-id="${task.id}" onclick="timeTracker.editTask('${task.id}')">
                <div class="month-task-time">${timeStr}</div>
                <div class="month-task-description">${this.escapeHtml(task.description)}</div>
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
        
        // Convert datetime-local inputs to UTC ISO strings for consistent backend storage
        const startTimeLocal = formData.get('start_time');
        const endTimeLocal = formData.get('end_time');
        
        const taskData = {
            description: formData.get('description'),
            start_time: new Date(startTimeLocal).toISOString(),
            end_time: new Date(endTimeLocal).toISOString(),
            reference_tickets: formData.get('reference_tickets')
                ? formData.get('reference_tickets').split(',').map(s => s.trim()).filter(s => s)
                : []
        };

        // Validation using local time objects for comparison
        if (new Date(startTimeLocal) >= new Date(endTimeLocal)) {
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
        // Format date for datetime-local input in user's local timezone
        // HTML datetime-local inputs expect YYYY-MM-DDTHH:MM format in local time
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day}T${hours}:${minutes}`;
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