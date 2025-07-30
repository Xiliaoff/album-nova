import http.server
import socketserver
import os
import shutil
from urllib.parse import unquote

PORT = 2010
BASE_DIR = "photos"

# Participants et images locales (modifie ici les chemins exacts)
participants = {
    
    "test": [
        r"e:\maison\dev\concour photo site\photos\steven praud\dsfghztreg.PNG",
        r"file:///C:/Users/poppm/Downloads/search%20(2).htm",
    ],
}

def prepare_photos():
    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)
    for participant, paths in participants.items():
        participant_dir = os.path.join(BASE_DIR, participant)
        if not os.path.exists(participant_dir):
            os.mkdir(participant_dir)
        for path in paths:
            if os.path.isfile(path):
                dest = os.path.join(participant_dir, os.path.basename(path))
                if not os.path.exists(dest):
                    try:
                        shutil.copy2(path, dest)
                        print(f"Copié {path} dans {dest}")
                    except Exception as e:
                        print(f"Erreur copie {path}: {e}")
            else:
                print(f"Fichier non trouvé : {path}")

def scan_photos():
    data = {}
    if not os.path.exists(BASE_DIR):
        return data
    for participant in sorted(os.listdir(BASE_DIR)):
        participant_path = os.path.join(BASE_DIR, participant)
        if os.path.isdir(participant_path):
            images = []
            for file in sorted(os.listdir(participant_path)):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    images.append(f"{participant}/{file}")
            if images:
                data[participant] = images
    return data

def generate_html(data):
    buttons = ''.join(f'<button onclick="showParticipant(\'{p}\')">{p}</button>' for p in data)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<title>album-nova</title>
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(160deg, #1f1f1f, #2b2b2b);
        color: #ddd;
        padding: 20px;
    }}
    h1 {{
        text-align: center;
        font-size: 2.8em;
        margin-bottom: 30px;
        color: #42f57b;
        text-shadow: 2px 2px 0 #222;
        letter-spacing: 2px;
    }}
    .barre {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        margin-bottom: 25px;
    }}
    .barre button {{
        background-color: #2d2f34;
        color: #42f57b;
        border: 2px solid #42f57b;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 1em;
        cursor: pointer;
        box-shadow: 0 0 8px #1d1f20;
        transition: all 0.2s ease;
    }}
    .barre button:hover {{
        background-color: #3b3f45;
        transform: scale(1.05);
        box-shadow: 0 0 12px #42f57b;
    }}
    #participant-name {{
        text-align: center;
        font-size: 1.8em;
        margin-bottom: 20px;
        color: #74f2ce;
        text-shadow: 1px 1px 2px #000;
    }}
    #images {{
        display: grid;
        grid-template-columns: repeat(auto-fill,minmax(140px,1fr));
        gap: 20px;
        justify-items: center;
    }}
    .img-container {{
        position: relative;
        user-select: none;
    }}
    /* Petit cœur en haut à droite si favori */
    .img-container.favori::after {{
        content: "❤";
        position: absolute;
        top: 6px;
        right: 6px;
        font-size: 20px;
        color: #ff4f4f;
        background: rgba(0,0,0,0.6);
        border-radius: 50%;
        padding: 3px 6px;
        pointer-events: none;
        z-index: 2;
    }}
    .img-container img {{
        width: 140px;
        height: 100px;
        object-fit: cover;
        border-radius: 6px;
        border: 2px solid #42f57b;
        background-color: #1a1a1a;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .img-container img:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 15px #42f57b88;
    }}
    /* Modal */
    #modal {{
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.95);
        justify-content: center;
        align-items: center;
        z-index: 1000;
        flex-direction: column;
    }}
    #modal img {{
        max-width: 90vw;
        max-height: 80vh;
        border-radius: 10px;
        box-shadow: 0 0 20px #42f57b88;
        border: 4px solid #42f57b;
        transition: border-color 0.3s, box-shadow 0.3s;
    }}
    #modal.gold img {{
        border-color: gold;
        box-shadow: 0 0 30px gold;
    }}
    #modal-close {{
        position: absolute;
        top: 20px;
        right: 30px;
        font-size: 35px;
        color: #eee;
        cursor: pointer;
        user-select: none;
    }}
    #modal-prev, #modal-next {{
        position: fixed;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(66,245,123,0.2);
        border: 2px solid #42f57b;
        font-size: 30px;
        color: #42f57b;
        padding: 10px 16px;
        cursor: pointer;
        border-radius: 6px;
        user-select: none;
        transition: background 0.3s;
    }}
    #modal-prev:hover, #modal-next:hover {{
        background: rgba(66,245,123,0.5);
    }}
    #modal-prev {{ left: 20px; }}
    #modal-next {{ right: 20px; }}

    /* Menu contextuel personnalisé */
    #context-menu {{
        position: absolute;
        background: #2d2f34;
        border: 1px solid #42f57b;
        border-radius: 6px;
        padding: 6px 0;
        display: none;
        z-index: 1100;
        box-shadow: 0 0 10px #42f57baa;
        user-select: none;
        min-width: 140px;
    }}
    #context-menu button {{
        background: none;
        border: none;
        color: #42f57b;
        padding: 8px 16px;
        width: 100%;
        text-align: left;
        cursor: pointer;
        font-weight: bold;
        font-size: 1em;
        transition: background 0.2s;
    }}
    #context-menu button:hover {{
        background: #42f57b22;
    }}

    footer {{
        margin-top: 40px;
        text-align: center;
        font-size: 0.9em;
        color: #999;
    }}
</style>
</head>
<body>
<h1>album-nova</h1>
<div class="barre">{buttons}</div>
<div id="participant-name"></div>
<div id="images"><p style="text-align:center; color:#888;">Cliquez sur une catégorie pour voir les photos</p></div>

<!-- Modal d'affichage agrandi -->
<div id="modal">
    <span id="modal-close" title="Fermer">&times;</span>
    <button id="modal-prev" title="Image précédente">&#10094;</button>
    <img id="modal-img" src="" alt="Image agrandie" />
    <button id="modal-next" title="Image suivante">&#10095;</button>
</div>

<!-- Menu contextuel personnalisé -->
<div id="context-menu">
    <button id="fav-btn">Mettre en favori</button>
</div>

<script>
const data = {data};
let currentImages = [];
let currentIndex = 0;
let currentImgElement = null;  // image cliquée (élément DOM)
const favoris = new Set(JSON.parse(localStorage.getItem('favoris') || '[]'));

function saveFavoris() {{
    localStorage.setItem('favoris', JSON.stringify(Array.from(favoris)));
}}

function isFavori(imgPath) {{
    return favoris.has(imgPath);
}}

function toggleFavori(imgPath) {{
    if(favoris.has(imgPath)) {{
        favoris.delete(imgPath);
    }} else {{
        favoris.add(imgPath);
    }}
    saveFavoris();
}}

function showParticipant(name) {{
    currentImages = data[name] || [];
    currentIndex = 0;
    document.getElementById('participant-name').textContent = name;
    const container = document.getElementById('images');
    container.innerHTML = '';
    if(currentImages.length === 0) {{
        container.innerHTML = '<p>Aucune image pour ce participant.</p>';
        return;
    }}
    currentImages.forEach((img, i) => {{
        const div = document.createElement('div');
        div.className = 'img-container';
        if(isFavori(img)) div.classList.add('favori');

        const image = document.createElement('img');
        image.src = '/photos/' + img;
        image.alt = img;
        image.dataset.index = i;

        // clic gauche = ouvrir modal
        image.onclick = () => showModal(i);

        // clic droit = ouvrir menu contextuel
        image.oncontextmenu = (e) => {{
            e.preventDefault();
            currentImgElement = image;
            showContextMenu(e.pageX, e.pageY, img);
        }};

        div.appendChild(image);
        container.appendChild(div);
    }});
    hideContextMenu();
}}

function showModal(index) {{
    currentIndex = index;
    const modal = document.getElementById('modal');
    const modalImg = document.getElementById('modal-img');
    const imgPath = currentImages[currentIndex];
    modalImg.src = '/photos/' + imgPath;
    modalImg.alt = imgPath;

    if(isFavori(imgPath)) {{
        modal.classList.add('gold');
    }} else {{
        modal.classList.remove('gold');
    }}

    modal.style.display = 'flex';
    hideContextMenu();
}}

document.getElementById('modal-close').onclick = () => {{
    document.getElementById('modal').style.display = 'none';
}};

document.getElementById('modal-prev').onclick = () => {{
    if(currentIndex > 0) {{
        currentIndex--;
        showModal(currentIndex);
    }}
}};

document.getElementById('modal-next').onclick = () => {{
    if(currentIndex < currentImages.length - 1) {{
        currentIndex++;
        showModal(currentIndex);
    }}
}};

// Menu contextuel

const contextMenu = document.getElementById('context-menu');
const favBtn = document.getElementById('fav-btn');

function showContextMenu(x, y, imgPath) {{
    favBtn.textContent = isFavori(imgPath) ? 'Retirer des favoris' : 'Mettre en favori';
    favBtn.onclick = () => {{
        toggleFavori(imgPath);
        // Mise à jour affichage grille (favori = petit cœur)
        showParticipant(document.getElementById('participant-name').textContent);
        // Mise à jour modal si ouvert sur cette image
        if(document.getElementById('modal').style.display === 'flex' &&
           currentImages[currentIndex] === imgPath) {{
            if(isFavori(imgPath)) {{
                document.getElementById('modal').classList.add('gold');
            }} else {{
                document.getElementById('modal').classList.remove('gold');
            }}
        }}
        hideContextMenu();
    }};
    contextMenu.style.left = x + 'px';
    contextMenu.style.top = y + 'px';
    contextMenu.style.display = 'block';
}}

function hideContextMenu() {{
    contextMenu.style.display = 'none';
    currentImgElement = null;
}}

// Clic ailleurs ferme le menu contextuel
window.addEventListener('click', (e) => {{
    if(!contextMenu.contains(e.target)) {{
        hideContextMenu();
    }}
}});
// Touche echap ferme aussi menu
window.addEventListener('keydown', (e) => {{
    if(e.key === 'Escape') {{
        hideContextMenu();
        document.getElementById('modal').style.display = 'none';
    }}
}});

// Fermer modal clic hors image
window.onclick = (event) => {{
    const modal = document.getElementById('modal');
    if(event.target === modal) {{
        modal.style.display = 'none';
    }}
}};

</script>

<footer>
    Créé par <strong>Steven Praud</strong>
</footer>
</body>
</html>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/index.html']:
            data = scan_photos()
            html = generate_html(data)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path.startswith('/photos/'):
            filepath = '.' + unquote(self.path)
            if os.path.isfile(filepath):
                self.send_response(200)
                ext = filepath.split('.')[-1].lower()
                mime_types = {
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif',
                    'bmp': 'image/bmp'
                }
                ctype = mime_types.get(ext, 'application/octet-stream')
                self.send_header('Content-type', ctype)
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Fichier non trouvé")
        else:
            super().do_GET()

def run():
    print("🏗  Préparation des photos...")
    print("⚙️  les photos charge...")
    prepare_photos()
    print(f"🔚  Serveur lancé sur http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑  Serveur arrêté.")

if __name__ == '__main__':
    run()