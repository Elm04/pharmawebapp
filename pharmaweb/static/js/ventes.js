document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const inputRecherche = document.getElementById('recherche-medicament');
    const resultatsRecherche = document.getElementById('resultats-recherche');
    const listePanier = document.getElementById('liste-panier');
    const montantTotal = document.getElementById('montant-total');
    const btnValider = document.getElementById('btn-valider-panier');
    const modalTicket = new bootstrap.Modal(document.getElementById('modalTicket'));
    
    // Recherche en temps réel
    inputRecherche.addEventListener('input', function() {
        const term = this.value.trim();
        
        if (term.length >= 2 || term.length === 0) {
            fetch(`/ventes/recherche-medicaments?q=${encodeURIComponent(term)}`)
                .then(response => response.text())
                .then(html => {
                    resultatsRecherche.innerHTML = html;
                    setupAjoutPanier();
                });
        }
    });
    
    // Configurer les boutons d'ajout
    function setupAjoutPanier() {
        document.querySelectorAll('.btn-ajouter').forEach(btn => {
            btn.addEventListener('click', function() {
                const medicamentId = this.dataset.id;
                const quantite = this.closest('.list-group-item').querySelector('.quantite').value;
                
                ajouterAuPanier(medicamentId, quantite);
            });
        });
    }
    
    // Ajouter un médicament au panier
    function ajouterAuPanier(medicamentId, quantite) {
        fetch('/ventes/ajouter-au-panier', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                medicament_id: medicamentId,
                quantite: quantite
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                afficherPanier(data.panier, data.total);
            } else {
                alert(data.message);
            }
        });
    }
    
    // Afficher le panier
    function afficherPanier(panier, total) {
        if (!panier || panier.length === 0) {
            listePanier.innerHTML = `
                <li class="list-group-item text-center text-muted">
                    Panier vide
                </li>
            `;
            montantTotal.textContent = '0.00 Fc';
            return;
        }
        
        let html = '';
        panier.forEach((item, index) => {
            html += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${item.nom}</strong>
                        <span class="text-muted small">x ${item.quantite}</span>
                    </div>
                    <div>
                        <span class="badge bg-primary rounded-pill">
                            ${(item.prix * item.quantite).toFixed(2)} Fc
                        </span>
                        <button class="btn btn-sm btn-danger ms-2 btn-retirer" data-index="${index}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </li>
            `;
        });
        
        listePanier.innerHTML = html;
        montantTotal.textContent = `${total.toFixed(2)} Fc`;
        
        // Boutons de suppression
        document.querySelectorAll('.btn-retirer').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                retirerDuPanier(index);
            });
        });
    }
    
    // Retirer un élément du panier
    function retirerDuPanier(index) {
        fetch('/ventes/retirer-du-panier', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ index: index })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                afficherPanier(data.panier, data.total);
            }
        });
    }
    
    // Valider la vente
    btnValider.addEventListener('click', function() {
        const modePaiement = document.getElementById('mode-paiement').value;
        const montantRegle = parseFloat(document.getElementById('montant-regle').value);
        const total = parseFloat(montantTotal.textContent);
        
        if (!modePaiement) {
            alert('Veuillez sélectionner un mode de paiement');
            return;
        }
        
        if (isNaN(montantRegle) {
            alert('Veuillez entrer un montant valide');
            return;
        }
        
        if (montantRegle < total) {
            alert('Le montant réglé est insuffisant');
            return;
        }
        
        fetch('/ventes/finaliser-vente', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mode_paiement: modePaiement,
                montant_regle: montantRegle
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                genererTicket(data.ticket);
                modalTicket.show();
            } else {
                alert(data.message);
            }
        });
    });
    
    // Générer le ticket
    function genererTicket(ticket) {
        document.getElementById('ticket-numero').textContent = ticket.numero;
        
        let itemsHtml = '';
        ticket.items.forEach(item => {
            itemsHtml += `
                <tr>
                    <td>${item.nom}</td>
                    <td class="text-end">${item.quantite}</td>
                    <td class="text-end">${item.prix.toFixed(2)} Fc</td>
                    <td class="text-end">${(item.prix * item.quantite).toFixed(2)} Fc</td>
                </tr>
            `;
        });
        
        const ticketHtml = `
            <div class="ticket">
                <h6 class="text-center mb-3">Pharmacie XYZ</h6>
                <p class="text-center small">${ticket.date}</p>
                <p>Ticket #${ticket.numero}</p>
                <p>Caissier: ${ticket.caissier}</p>
                
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Produit</th>
                            <th class="text-end">Qté</th>
                            <th class="text-end">Prix</th>
                            <th class="text-end">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${itemsHtml}
                    </tbody>
                </table>
                
                <div class="d-flex justify-content-between border-top pt-2">
                    <strong>Total:</strong>
                    <strong>${ticket.total.toFixed(2)} Fc</strong>
                </div>
                
                <div class="d-flex justify-content-between">
                    <span>Montant réglé:</span>
                    <span>${ticket.montant_regle.toFixed(2)} Fc</span>
                </div>
                
                <div class="d-flex justify-content-between">
                    <span>Monnaie:</span>
                    <span>${ticket.monnaie.toFixed(2)} Fc</span>
                </div>
                
                <p class="text-center mt-3 small">Merci de votre visite !</p>
            </div>
        `;
        
        document.getElementById('ticket-content').innerHTML = ticketHtml;
    }
    
    // Imprimer le ticket
    document.querySelector('.btn-print').addEventListener('click', function() {
        const printContent = document.getElementById('ticket-content').innerHTML;
        const originalContent = document.body.innerHTML;
        
        document.body.innerHTML = printContent;
        window.print();
        document.body.innerHTML = originalContent;
        window.location.reload();
    });
    
    // Initialisation
    setupAjoutPanier();
});