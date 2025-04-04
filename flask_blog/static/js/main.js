document.addEventListener('DOMContentLoaded', function() {
    // Reply to comment functionality
    const replyLinks = document.querySelectorAll('.reply-link');
    
    replyLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const commentId = this.getAttribute('data-comment-id');
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            
            // Toggle the reply form
            if (replyForm.style.display === 'none' || replyForm.style.display === '') {
                replyForm.style.display = 'block';
                // Set the parent comment ID in the hidden field
                const parentIdField = replyForm.querySelector('input[name="parent_id"]');
                if (parentIdField) {
                    parentIdField.value = commentId;
                }
            } else {
                replyForm.style.display = 'none';
            }
        });
    });

    // Post form handling
    const contentTextarea = document.getElementById('content');
    if (contentTextarea) {
        // Add autoresize functionality to the textarea
        contentTextarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    // Post delete confirmation
    const deletePostForms = document.querySelectorAll('.delete-post-form');
    deletePostForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Comment delete confirmation
    const deleteCommentForms = document.querySelectorAll('.delete-comment-form');
    deleteCommentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this comment? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Multiple select styling for tags
    const tagSelect = document.getElementById('tags');
    if (tagSelect) {
        tagSelect.classList.add('form-select');
        tagSelect.setAttribute('multiple', 'multiple');
        tagSelect.setAttribute('size', '5');
    }

    // Flash message auto-close
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000); // Close after 5 seconds
    });
});
