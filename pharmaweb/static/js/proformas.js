document.addEventListener('DOMContentLoaded', function() {
    // Ajout produit via AJAX
    document.querySelectorAll('.btn-ajouter-proforma').forEach(btn => {
        btn.addEventListener('click', function() {
            const medicamentId = this.dataset.id;
            const quantite = this.closest('.card').querySelector('.quantite-input').value;
            
            fetch("{{ url_for('views.ajouter_produit_proforma') }}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    medicament_id: medicamentId,
                    quantite: quantite
                })
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    location.reload(); // Rafraîchir pour voir les changements
                }
            });
        });
    });
});