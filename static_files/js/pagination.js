// Pagination JavaScript with Prefetching
document.addEventListener('DOMContentLoaded', function() {
    // Event delegation for pagination clicks
    document.addEventListener('click', async function(e) {
        const pageLink = e.target.closest('.page-link');
        const content = document.getElementById('content');
        if (!pageLink) return;
        
        e.preventDefault();
        const url = pageLink.href;

        
        try {
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error('Network error');
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update content and pagination
            content.innerHTML = 
                doc.getElementById('content').innerHTML;
            
            window.history.pushState({}, '', url);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (error) {
            console.error('Error:', error);
            window.location.href = url;
        } finally {
                //
        }
    });

    // Prefetch pages on hover
    document.addEventListener('mouseover', function(e) {
        const pageLink = e.target.closest('.page-link');
        if (!pageLink) return;
        
        const url = pageLink.href;
        if (!pageLink.dataset.prefetched) {
            fetch(url, {
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                priority: 'low'
            });
            pageLink.dataset.prefetched = true;
        }
    });

    // Handle browser history
    window.addEventListener('popstate', function() {
        window.location.reload();
    });
});