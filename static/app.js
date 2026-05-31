document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('.toggle-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            const todoId = this.dataset.todoId;

            try {
                const response = await fetch(`/toggle/${todoId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    this.closest('.todo-item').classList.toggle('completed');
                }
            } catch (error) {
                console.error('Error toggling todo:', error);
                this.checked = !this.checked;
            }
        });
    });
});
