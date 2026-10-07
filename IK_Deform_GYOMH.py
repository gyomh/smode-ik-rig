#    #########      ###         ###      #########      #########         ###############
# ###               ######   ######   ###         ###   ###      ###      ###
# ###               ###   ###   ###   ###         ###   ###         ###   ###
#    #########      ###   ###   ###   ###         ###   ###         ###   ############
#             ###   ###         ###   ###         ###   ###         ###   ###
#             ###   ###         ###   ###         ###   ###      ###      ###
# ############      ###         ###      #########      #########         ###############
#
# -------------------- "Guillaume Henrion aka [GYOMH]" "07/10/2026" --------------------
# __________________________________________ ___________________________________________
# |                                       | |                                         |
# |    IK DEFORM                          | | Deformation d'objet 3D par rig IK / FK  |
# |       V0.4                            | | - Points (poignees) dans l'objet        |
# |                                       | | - Le rig deforme la geometrie           |
# |_______________________________________| |_________________________________________|
# |    Instructions :                     | | - Modifiers Transform3d + masques       |
# | 1- Coller le script : il cree son     | |   lineaires (poids doux)                |
# |    groupe 3D (ou le placer dans un)   | | - Poignees a icone, face camera         |
# | 2- Glisser l objet 3D (capsule) dans  | | - Setup Pivots : placer les points      |
# |    le groupe : le rig se cree seul    | | - Banks Manual Setup / Animation        |
# | 3- Placer les points, puis animer     | | - IK / FK, Flip Bend, Limit 180,        |
# |    les poignees                       | |   angle min / max de IK1                |
# |_______________________________________| |_________________________________________|
#
# HISTORIQUE
# V0.1 - 07/10/2026 - Version initiale, derivee de IK Rig V1.14 : au lieu de deplacer des elements-bones, le rig
#                      deforme UN objet 3D (capsule verticale) : un Transform3dGeometryModifier par articulation
#                      (pivot = articulation, rotation relative, masque lineaire = zone de transition Blend Width).
# V0.2 - 07/10/2026 - Objet quelconque (boite / parallelepipede, capsule, plan) : axe, longueur et pivot deduits de la
#                      geometrie (bone_axis), orientation du calque prise en compte (horizontal OK) ; subdivision de
#                      l'axe (Height Precision de la capsule, Precision x/y/z de la boite, uniforme decouplee).
# V0.3 - 07/10/2026 - Bank Manual Setup : 2D Mode (Planar) en haut du bank (case : 2D / decochee : 3D).
# V0.4 - 07/10/2026 - Tous les generateurs de geometrie : Capsule, Cylinder, Box, Plane, Rectangle, Sphere, Torus, Circle,
#                      Star (axe, longueur, pivot et subdivision deduits ; precisions uniformes decouplees). Autres
#                      types : message d'avertissement.
#

bones: Oil.createObject("OwnedVector(WeakPointer(Layer))")
boneCount: Oil.PositiveInteger(2)
enableIK: Oil.Boolean(True)
setupPivots: Oil.Boolean(False)
lockBones: Oil.Boolean(True)
planarMode: Oil.Boolean(False)
fkMode: Oil.Boolean(False)
boneRotation: Oil.createObject("Angle")
reverseAxis: Oil.Boolean(False)
createRig: Oil.Boolean(False)
jointLimits: Oil.createObject("OwnedVector(Boolean)")
jointFlips: Oil.createObject("OwnedVector(Boolean)")
showJoints: Oil.Boolean(True)
jointDiameter: Oil.PositiveMeters(0.1)
rigData: Oil.String("")
autoMode: Oil.Boolean(True)
blendWidth: Oil.PositiveMeters(0.4)
ik1Min: Oil.createObject("Angle")
ik1Max: Oil.createObject("Angle")
resetRig: Oil.Boolean(False)

import math
import json

# --- IK chaine de N bones (FABRIK 3D), rig cree par le script -------------------------
# 1. Creer N elements (ex. 3 plans textures : bras, avant-bras, main). Longueur, axe et pivot
#    sont deduits de la geometrie : capsule (axe Y, pivot a la base), plan (largeur ou hauteur
#    la plus grande, pivot = ancrage), boite (axe le plus long, pivot au centre). Les
#    articulations (nulls) sont toujours aux EXTREMITES des bones, le pivot de l'element est
#    deplace en consequence. Reverse Axis : inverse le sens de l'element (base a l'autre bout).
# 2. Regler Bone Count : le nombre d'emplacements de la liste Bones s'ajuste.
# 3. Glisser-deposer les elements dans Bones (ordre : racine -> pointe).
# 4. Cliquer Create Rig. Le script cree le groupe IK_Rig (Group3dLayer) qui contient les nulls
#    IK_Joint_1..N (base de chaque bone), IK_Cible (pointe du dernier bone) et les spheres, empile
#    les bones bout a bout (longueur = geometrie de chaque bone) a partir de la position du premier
#    bone, et lance l'IK.
# Controleurs = POIGNEES, tous deplacables : IK_Joint_1 (racine), IK_Joint_2..N (articulations : on tire
# la chaine par un coude, les longueurs restent fixes), IK_Cible (pointe). Ce sont des plans portant
# l'icone IconFleche (croix a quatre fleches), dont le materiau est PARTAGE : un MaterialBank dans le
# groupe, reference par chaque poignee (cree par le script s'il manque ; modifier le materiau modifie
# toutes les poignees). Toujours a plat face a la camera de la Compo (camera courante, sinon par defaut ;
# tous types de placement : orbitale, position+orientation, look-at, matrice), en 2D comme en 3D :
# plan parallele a l'ecran, meme dans des groupes imbriques. Elles sont dessinees par-dessus (test de profondeur coupe). Show Joints
# les affiche / masque (inactives = absentes du rendu) ; tant qu'elles sont visibles, IK_Info previent
# de les masquer avant le rendu. Taille = Joint Diameter (cote du plan).
# MONTAGE : placer le script dans un Group3dLayer (outils du groupe) avec les N elements : le groupe EST le
# rig (poignees, texte, MaterialBank, banks y sont crees), deplacable et imbricable dans un autre rig. Ancien
# montage (script dans une Compo) : le rig est cree dans un sous-groupe IK_Rig ; les bones, restes a la racine
# de la Compo, suivent par la transformation du groupe. Garder l'echelle du groupe a 1.
# Le calcul part de la pose courante de la chaine : le cote du pli est memorise, il ne saute pas.
# Setup Pivots : coche = le rig est fige et les nulls (IK_Joint_n, IK_Cible) se deplacent librement,
# par exemple pour les poser sur les trous des textures. Decoche = les nulls deviennent les nouvelles
# articulations : longueurs recalculees, chaque element reste colle a son bone dans la position ou
# il est a cet instant (rig "manuel"). Create Rig recalcule tout depuis la geometrie (efface le reglage).
# Flip Bend n = etat (case), un par articulation : coche = le pli est de l'autre cote ; chaque changement de la
# case passe l'articulation n de l'autre cote de la droite formee par ses deux voisines (symetrie).
# Limit 180 (entre deux bones, bank Manual Setup) : l'articulation ne plie plus que d'un seul cote (180 degres).
# Bone Rotation (parametre) = 'Bone3 Rotation' dans le bank Animation tools (le numero suit Bone Count) :
# angle ; fait tourner la main (dernier bone) autour de l'articulation N (celle d'avant IK_Cible) ; ne
# change pas le calcul d'IK. A l'import, le script cree les banks et leurs Parameters lies s'ils manquent.
# IK_Info : texte d'info dans le groupe (verrouille, desactive sauf Setup Pivots / IK desactive / rig
# a recreer : jamais dans le rendu en usage normal). Messages (francais) dans MSG_* en tete du script.
# Largeur de la boite = largeur de la compo moins 3 % de marge de chaque cote (TEXT_MARGIN), retour
# a la ligne automatique, texte centre. Aspect : rouge, taille 40, fond noir a 45 % d'opacite.
# A l'import : cree les ParameterBank 'Animation tools' et 'Setup tools' dans la Compo s'ils manquent.
# Fk Mode (selecteur IK / FK) : decoche = IK (defaut) : la pointe reste sur la cible, tirer une
# articulation intermediaire (IK_Joint_2..N) plie la chaine. Coche = FK : tirer une articulation
# fait tourner les bones avant elle autour de la racine, et tout ce qui est apres (articulations,
# cible) suit comme un bloc rigide. Deplacer la racine ou la cible = toujours IK.
# Planar Mode : coche = 2D, toute la chaine reste dans le plan de la racine (z du groupe) ;
# decoche = 3D.
# Selection : Lock Bones (coche par defaut) verrouille (cadenas) les bones et les spheres
# d'articulation : seuls les nulls (IK_Joint_n, IK_Cible) se selectionnent dans la vue 3D.
# Create Rig recoche Lock Bones. Pendant Setup Pivots, les bones sont deverrouilles (les spheres
# restent verrouillees) ; ils se reverrouillent a la sortie. Decocher Lock Bones pour pouvoir
# selectionner les bones le reste du temps (ex. pour les repositionner avec IK coupe).
# Angles Oil en RADIANS ; ordre Euler 0 = Rz * Ry * Rx (colonnes de la matrice = axes monde).
# 2 bones : formule exacte. 3 bones et plus : FABRIK. N bones = N + 1 points, la cible guide la
# POINTE du dernier bone.

MIN_BONES, MAX_BONES = 2, 8
DEFAULT_BONES = 2                  # Bone Count apres une remise a zero
DEFAULT_DIAMETER = 0.1             # Joint Diameter par defaut
DEFAULT_BLEND = 0.4                # Blend Width par defaut (m)
DEFORM_PREFIX = 'IK_Deform_'       # modifiers crees sur l'objet
DEFORM_PRECISION = 64              # Height Precision mini de la capsule (sinon rien a plier)
# Code couleur des elements (couleur de repere des calques / outils, valeurs 0-255)
COL_BONE = (219, 230, 30)          # elements 3D (bones)
COL_RIG = (235, 69, 230)           # groupe IK_Rig et poignees (IK_Joint_n, IK_Cible) : rose
COL_MATERIALS = (104, 26, 101)     # MaterialBank des poignees et texte d'info IK_Info
COL_RESET = (255, 0, 0)            # bouton RESET : rouge
COL_SCRIPT = (220, 120, 237)       # le script IK_Deform
COL_BANKS = {'2 - Animation tools': (89, 230, 26), '1 - Manual Setup tools': (23, 112, 221)}
TEXT_SIZE = 40.0                   # texte d'info : taille
TEXT_COLOR = (255, 0, 0)           # texte d'info : rouge
TEXT_BG = (0, 0, 0)                # texte d'info : fond noir ...
TEXT_BG_ALPHA = 0.45               # ... a 45 % d'opacite
IMPORT_VERSION = 9                 # a incrementer quand l'initialisation a l'import change (rejouee une fois)
# Poignees (controleurs) : un plan par articulation + la cible, avec l'icone IconFleche (croix a quatre
# fleches), materiau PARTAGE dans un MaterialBank du groupe, reference par chaque poignee.
ICON_NAME = 'IconFleche'
ICON_SEGMENTS = [(0.05, 0.5, 0.95, 0.5), (0.05, 0.5, 0.2, 0.4), (0.05, 0.5, 0.2, 0.6), (0.95, 0.5, 0.8, 0.4), (0.95, 0.5, 0.8, 0.6),
                 (0.5, 0.05, 0.5, 0.95), (0.5, 0.05, 0.4, 0.2), (0.5, 0.05, 0.6, 0.2), (0.4, 0.8, 0.5, 0.95), (0.6, 0.8, 0.5, 0.95)]
ICON_STROKE = (1.0, 0.503597122302, 1.0)      # couleur du trait de l'icone (rose)
ICON_THICKNESS = 82.5                         # epaisseur du trait (px, texture 1024 x 1024)
RX90 = [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]]   # Rx(-90 deg) : le plan nait couche (plan XZ), on le dresse face a +Z
INFO_NAME = 'IK_Info'
TEXT_MARGIN = 0.03          # marge du texte d'info : 3 % de la largeur de la compo de chaque cote
SETUP_BANK = '1 - Manual Setup tools'
ANIM_BANK = '2 - Animation tools'
BANK_NAMES = (SETUP_BANK, ANIM_BANK)          # ordre de creation = ordre dans le groupe (Setup au-dessus)
LEGACY_BANKS = {'Setup tools': SETUP_BANK, 'Animation tools': ANIM_BANK}    # anciens noms, renommes a l'import
ROT_LABEL = 'Bone%d Rotation'      # '%d' = numero du dernier bone du rig (suit Bone Count)
# Contenu des deux banks, calcule d'apres le nombre de bones N : liste de (libelle, genre, reference, type).
# genre 'var' = variable du script (reference = son nom), 'bone' = emplacement k de Bones, 'limit' / 'flip' =
# booleen k-1 de jointLimits / jointFlips (un par articulation : N-1). Chaque Parameter est lie a sa cible par
# un ParameterLinkTarget ; le script cree / reconstruit ceux qui manquent (voir fill_bank).
def bank_spec(name, N):
    out = []
    if name == SETUP_BANK:
        out.append(('Auto Rig', 'var', 'autoMode', 'Boolean'))
        out.append(('2D Mode (Planar)', 'var', 'planarMode', 'Boolean'))
        out.append(('1 - Bone Count', 'var', 'boneCount', 'PositiveInteger'))
        out.append(('IK1 Angle Min', 'var', 'ik1Min', 'Angle'))
        out.append(('IK1 Angle Max', 'var', 'ik1Max', 'Angle'))
        out.append(('Object', 'bone', 1, None))        # l'objet 3D a deformer (un seul)
        for k in range(1, N):                          # entre deux bones : limite l'articulation a 180 degres
            out.append(('Limit 180\u00b0 %d-%d' % (k, k + 1), 'limit', k, 'Boolean'))
        out.append(('Blend Width', 'var', 'blendWidth', 'PositiveMeters'))
        out.append(('2 - Create Rig', 'var', 'createRig', 'Boolean'))
        out.append(('3 - Setup Pivots', 'var', 'setupPivots', 'Boolean'))
        out.append(('\u26a0 RESET \u26a0', 'var', 'resetRig', 'Boolean'))
    else:
        out.append(('Show Joints', 'var', 'showJoints', 'Boolean'))
        out.append(('FK Mode', 'var', 'fkMode', 'Boolean'))
        for k in range(1, N):                          # un retournement de pli par articulation
            out.append(('Flip Bend %d' % k, 'flip', k, 'Boolean'))
    return out
# Texte d'info (calque IK_Info dans le groupe, verrouille). Il n'est ACTIF que dans les cas listes
# ci-dessous, sinon il est desactive pour ne pas apparaitre dans le rendu / l'export.
MSG_SETUP = 'RÉGLAGE DES POINTS : placez les poignées sur les articulations de l\'objet. Décochez Setup Pivots pour valider.'
MSG_JOINTS = 'Poignées visibles : décochez Show Joints avant le rendu'
MSG_IK_OFF = 'IK désactivé'
MSG_RIG = 'Rig à recréer : cliquez sur Create Rig'
MSG_DROP = 'Déposez l\'objet 3D à déformer dans Object'
MSG_UNKNOWN = 'Objet de type %s non géré : axe Y et 1 m par défaut'
MSG_DRAG = 'Glissez l\'objet 3D à déformer (capsule) dans ce groupe 3D'
GROUP_NAME = 'IK_Rig'
NULL_PREFIX = 'IK_Joint_'
TARGET_NAME = 'IK_Cible'
SPHERE_PREFIX = 'IK_Sphere_'        # ancien marqueur (supprime : les poignees le remplacent)
LEGACY_NAMES = ('IK_Pole',)

# ---- etat propre a chaque script ----
# Les scripts Smode partagent le meme espace de noms global : deux rigs (bras + jambe) se perturberaient
# (pose memorisee, detection de tirage, drapeaux d'import). L'etat est donc range par script, indexe par sa
# compo (l'objet Python d'un meme element Smode est toujours le meme tant qu'on le garde reference).
def S():
    reg = globals().setdefault('_IK_REGISTRY', [])
    comp = script.parentElement
    for c, d in reg:
        if c is comp:
            return d
    d = {}
    reg.append((comp, d))
    return d


# ---- vecteurs ----
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def mul(a, k): return (a[0]*k, a[1]*k, a[2]*k)
def dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a): return math.sqrt(dot(a, a))
def unit(a, fallback):
    n = norm(a)
    return mul(a, 1.0 / n) if n > 1e-9 else fallback
def perp(v, u): return sub(v, mul(u, dot(v, u)))

# ---- matrices 3x3 : M[i][j] = composante i de l'axe j ----
def mmul(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mtr(A): return [[A[j][i] for j in range(3)] for i in range(3)]
def frame(x, ref):
    # axe X = x ; axe Y = ref perpendiculaire a x ; Z = X ^ Y
    x = unit(x, (1.0, 0.0, 0.0))
    y = unit(perp(ref, x), unit(perp((0.0, 1.0, 0.0), x), unit(perp((0.0, 0.0, 1.0), x), (0.0, 1.0, 0.0))))
    z = cross(x, y)
    return [[x[0], y[0], z[0]], [x[1], y[1], z[1]], [x[2], y[2], z[2]]]
def flat(M): return [M[i][j] for i in range(3) for j in range(3)]
def unflat(f): return [[f[0], f[1], f[2]], [f[3], f[4], f[5]], [f[6], f[7], f[8]]]
def euler_to_m(ex, ey, ez):
    cx, sx, cy, sy, cz, sz = math.cos(ex), math.sin(ex), math.cos(ey), math.sin(ey), math.cos(ez), math.sin(ez)
    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return mmul(mmul(Rz, Ry), Rx)
def frames_for(dirs, nref):
    # repere de chaque bone : axe X = direction du bone, Z du monde = "haut" (comme un look-at) ; meme
    # definition en 2D et en 3D (pas de saut au changement de mode, la face avant des plans reste fixe)
    out = []
    for d in dirs:
        up = cross((0.0, 0.0, 1.0), d)
        out.append(frame(d, up) if norm(up) > 1e-3 else frame(d, nref))
    return out
def m_to_euler(R):
    ey = -math.asin(max(-1.0, min(1.0, R[2][0])))
    if abs(R[2][0]) < 0.99999:
        ex = math.atan2(R[2][1], R[2][2])
        ez = math.atan2(R[1][0], R[0][0])
    else:
        ex = 0.0
        ez = math.atan2(-R[0][1], R[1][1])
    return ex, ey, ez

# ---- acces aux layers ----
def pos(layer):
    p = layer.placement.position
    return (p.x.get(), p.y.get(), p.z.get())
def set_pos(layer, v):
    p = layer.placement.position
    p.x = float(v[0]); p.y = float(v[1]); p.z = float(v[2])
def get_rot(layer):
    o = layer.placement.orientation
    return euler_to_m(o.x.get(), o.y.get(), o.z.get())
def set_rot(layer, R):
    ex, ey, ez = m_to_euler(R)
    o = layer.placement.orientation
    o.x = ex; o.y = ey; o.z = ez
def lab(layer): return str(layer.label.get())

def group_transform(grp):
    # (X, Y, Z, W, R) : colonnes de la worldMatrix du groupe ; R = rotation (colonnes normalisees)
    ident = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
    if grp is None:
        cols = ident
    else:
        m = grp.worldMatrix
        cols = tuple((c.x.get(), c.y.get(), c.z.get()) for c in (m.x, m.y, m.z, m.w))
        if min(norm(c) for c in cols[:3]) < 1e-6:        # matrice pas encore evaluee
            cols = ident
    nx, ny, nz = (unit(c, d) for c, d in zip(cols[:3], ident[:3]))
    R = [[nx[0], ny[0], nz[0]], [nx[1], ny[1], nz[1]], [nx[2], ny[2], nz[2]]]
    return cols[0], cols[1], cols[2], cols[3], R

def to_world(G, p):
    X, Y, Z, W, R = G
    return add(add(add(mul(X, p[0]), mul(Y, p[1])), mul(Z, p[2])), W)

def set_lock(layer, locked):
    # cadenas du calque (non selectionnable dans la vue 3D) : editable = ActivationState (2 = inactif),
    # set() attend un BOOLEEN (True = actif / modifiable)
    st = layer.editable
    if (st.get() == 2) != locked:
        st.set(not locked)

def bone_axis(layer):
    # deduit de la geometrie : (axe local de longueur E, longueur L ou None, decalage du pivot po,
    # normale locale U ou None). po = distance de la BASE du bone au pivot, le long de E
    # (0 = pivot a la base, L/2 = pivot au centre). U = face avant (plans) : fixe le roulis.
    g = layer.generator
    sc = layer.placement.size
    try:
        if hasattr(g, 'height'):                      # capsule / cylindre : pivot a la base, axe Y
            return (0.0, 1.0, 0.0), g.height.get() * abs(sc.y.get()), 0.0, None
    except Exception:
        pass
    try:
        if hasattr(g, 'anchor') and hasattr(g.size, 'width'):
            # plan (PlaneGeometryGenerator) : largeur le long de X, hauteur le long de Z, normale Y
            w = g.size.width.get() * abs(sc.x.get())
            h = g.size.height.get() * abs(sc.z.get())
            if w >= h:
                return (1.0, 0.0, 0.0), w, g.anchor.x.get() * w, (0.0, -1.0, 0.0)
            return (0.0, 0.0, 1.0), h, g.anchor.y.get() * h, (0.0, -1.0, 0.0)
    except Exception:
        pass
    try:
        if hasattr(g, 'size') and hasattr(g.size, 'x'):   # boite : centree sur le pivot
            dims = [g.size.x.get() * abs(sc.x.get()), g.size.y.get() * abs(sc.y.get()), g.size.z.get() * abs(sc.z.get())]
            k = dims.index(max(dims))
            axis = [0.0, 0.0, 0.0]; axis[k] = 1.0
            return tuple(axis), dims[k], dims[k] * 0.5, None
    except Exception:
        pass
    return (1.0, 0.0, 0.0), None, 0.0, None

def set_color(o, rgb):
    # couleur de repere (colorLabel) en valeurs 0-255
    c = o.colorLabel
    c.red.set(rgb[0] / 255.0)
    c.green.set(rgb[1] / 255.0)
    c.blue.set(rgb[2] / 255.0)

def tool_label(t):
    return str(t.label if isinstance(t.label, str) else t.label.get())

def bank_label(spec_label, N):
    return spec_label % N if '%d' in spec_label else spec_label

def is_spec_label(spec_label, label):
    # '%d' correspond a n'importe quel numero de bone
    if '%d' not in spec_label:
        return label.lower() == spec_label.lower()
    pre, post = spec_label.split('%d')
    mid = label[len(pre):len(label) - len(post)] if len(label) >= len(pre) + len(post) else ''
    return label.startswith(pre) and label.endswith(post) and mid.isdigit()

def make_bank_param(spec_label, var, typ, N, rgb):
    # Parameter(type) lie au parametre du script : valeur initiale = valeur courante du script, un
    # ParameterLinkTarget qui pointe sur la variable du script ; couleur = celle de son bank
    p = Oil.createObject('Parameter(%s)' % typ)
    p.label = bank_label(spec_label, N)
    set_color(p, rgb)
    target = getattr(script, var)
    p.value.set(target.get())
    lt = Oil.createObject('ParameterLinkTarget')
    lt.target.set(target)
    p.targets.append(lt)
    return p

def make_elem_param(label, typ, target, rgb):
    # Parameter lie a un element d'un vecteur du script (emplacement de Bones, booleen de jointLimits / jointFlips)
    p = Oil.createObject('Parameter(%s)' % typ)
    p.label = label
    set_color(p, rgb)
    cur = target.get()
    if cur is not None:                                    # element deja rempli : on ne le vide pas
        p.value.set(cur)
    lt = Oil.createObject('ParameterLinkTarget')
    lt.target.set(target)
    p.targets.append(lt)
    return p

def make_spec_param(item, N, rgb):
    label, kind, ref, typ = item
    if kind == 'var':
        return make_bank_param(label, ref, typ, N, rgb)
    if kind == 'bone':
        return make_elem_param(label, 'WeakPointer(Layer)', script.bones[ref - 1], rgb)
    vec = script.jointLimits if kind == 'limit' else script.jointFlips
    return make_elem_param(label, 'Boolean', vec[ref - 1], rgb)

def bone_param_index(label):
    # champ 'Object' (emplacement 1 de Bones) : 1, sinon 0
    return 1 if label == 'Object' else 0

def fill_bank(bank, name, N):
    # met le contenu du bank en accord avec bank_spec : on garde le debut identique (valeurs, animations, liens),
    # on retire la suite qui differe et on la recree (Bone Count change -> champs Bone / Limit / Flip en plus ou en moins)
    rgb = COL_BANKS[name]
    spec = bank_spec(name, N)
    have = [str(bank.parameters[j].label.get()) for j in range(len(bank.parameters))]
    p = 0
    while p < len(spec) and p < len(have) and (is_spec_label(ROT_LABEL, have[p]) if spec[p][0] == ROT_LABEL % N
                                                  else have[p].lower() == spec[p][0].lower()):
        p += 1
    for j in range(len(have) - 1, p - 1, -1):
        bank.parameters.removeAt(j)
    for item in spec[p:]:
        bank.parameters.append(make_spec_param(item, N, rgb))
    for j in range(len(bank.parameters)):                  # parametres encore sans couleur : couleur du bank
        c = bank.parameters[j].colorLabel
        if str(bank.parameters[j].label.get()).startswith('⚠'):      # bouton RESET : toujours rouge
            if abs(c.red.get() - 1.0) > 1e-3 or c.green.get() > 1e-3 or c.blue.get() > 1e-3:
                set_color(bank.parameters[j], COL_RESET)
        elif c.red.get() + c.green.get() + c.blue.get() < 1e-6:
            set_color(bank.parameters[j], rgb)

def sync_banks(comp, N):
    # chaque image : le contenu des banks suit le nombre de bones
    for i in range(len(comp.tools)):
        nm = tool_label(comp.tools[i])
        if nm in BANK_NAMES:
            fill_bank(comp.tools[i], nm, N)

def set_var(comp, var, value):
    # ecrit une valeur dans un parametre du script ET dans les Parameters de bank qui lui sont lies : un Parameter lie
    # repose sa propre valeur sur le script, une ecriture faite seulement cote script serait annulee (ex. Create Rig)
    var.set(value)
    for i in range(len(comp.tools)):
        t = comp.tools[i]
        if t.getOilClassName() != 'ParameterBank':
            continue
        for j in range(len(t.parameters)):
            p = t.parameters[j]
            for k in range(len(p.targets)):
                if p.targets[k].target.get() is var:
                    p.value.set(value)

def mirror_bones(comp, N):
    # champ 'Bone n' vide alors que l'emplacement n du script est rempli (depot dans le script) : le champ le reprend
    for i in range(len(comp.tools)):
        t = comp.tools[i]
        if t.getOilClassName() != 'ParameterBank' or tool_label(t) != SETUP_BANK:
            continue
        for j in range(len(t.parameters)):
            p = t.parameters[j]
            n = bone_param_index(str(p.label.get()))
            if 1 <= n <= N and p.value.get() is None and script.bones[n - 1].get() is not None:
                p.value.set(script.bones[n - 1].get())

def ensure_banks(comp, N):
    # cree les deux ParameterBank (1 - Manual Setup tools / 2 - Animation tools) et leurs Parameters lies, s'ils manquent
    labels = [tool_label(comp.tools[k]) for k in range(len(comp.tools))]
    for i in range(len(comp.tools)):
        old = tool_label(comp.tools[i])
        if old in LEGACY_BANKS and LEGACY_BANKS[old] not in labels:
            comp.tools[i].label = LEGACY_BANKS[old]          # ancien nom -> nouveau nom
    labels = [tool_label(comp.tools[k]) for k in range(len(comp.tools))]
    for name in BANK_NAMES:
        if name not in labels:
            b = Oil.createObject('ParameterBank')                  # banque neuve : on la remplit AVANT de l'ajouter
            b.label = name
            set_color(b, COL_BANKS[name])
            fill_bank(b, name, N)
            comp.tools.append(b)

def update_bank_labels(comp, N):
    # libelle 'Bone%d Rotation' : le numero suit le nombre de bones
    for i in range(len(comp.tools)):
        if tool_label(comp.tools[i]) == ANIM_BANK:
            bank = comp.tools[i]
            for j in range(len(bank.parameters)):
                p = bank.parameters[j]
                lb = str(p.label.get())
                if is_spec_label(ROT_LABEL, lb) and lb != ROT_LABEL % N:
                    p.label = ROT_LABEL % N

def style_text(l):
    # aspect du texte d'info : rouge, taille TEXT_SIZE, fond noir a TEXT_BG_ALPHA d'opacite
    st = l.generator.style
    st.size = TEXT_SIZE
    fg = st.foreground
    fg.red.set(TEXT_COLOR[0] / 255.0); fg.green.set(TEXT_COLOR[1] / 255.0); fg.blue.set(TEXT_COLOR[2] / 255.0)
    fg.alpha.set(1.0)
    bg = st.background
    bg.enabled.set(True)
    bg.value.red.set(TEXT_BG[0] / 255.0); bg.value.green.set(TEXT_BG[1] / 255.0); bg.value.blue.set(TEXT_BG[2] / 255.0)
    bg.value.alpha.set(TEXT_BG_ALPHA)

def make_text(name):
    # calque texte d'info : vide, desactive (rien dans le rendu) et verrouille
    l = Oil.createObject('TextLayer')
    l.label = name
    set_color(l, COL_MATERIALS)
    g = Oil.createObject('LocalTextGenerator')
    g.text.set('')
    l.generator = g
    style_text(l)
    r = Oil.createObject('DefaultTextRenderer')
    r.placement.position.x = 0.5                    # centre ; largeur = celle de la compo (voir apply_info)
    r.placement.position.y = 0.0747739
    r.size.width.type.set(1)                        # wordWrap : retour a la ligne si la phrase est trop longue
    r.size.height.type.set(0)                       # hauteur automatique
    r.style.alignment.set(0)                        # middleCenter : texte centre
    l.renderer = r
    l.activation.set(False)
    l.editable.set(False)
    return l

_frame = {'msgs': [], 'layer': None, 'width': 0.0}

def apply_info():
    # affiche les messages de l'image courante (un par ligne), ou desactive le calque texte s'il n'y en a pas
    t = _frame['layer']
    if t is None:
        return
    msg = '\n'.join(_frame['msgs']) if _frame['msgs'] else None
    set_lock(t, True)
    # boite de texte = largeur de la compo moins une marge de TEXT_MARGIN de chaque cote, retour a la
    # ligne automatique (wordWrap), boite centree, texte centre (middleCenter)
    r = t.renderer
    if r.size.width.type.get() != 1:
        r.size.width.type.set(1)
    if r.size.height.type.get() != 0:
        r.size.height.type.set(0)
    if r.style.alignment.get() != 0:
        r.style.alignment.set(0)
    w = float(_frame['width'] or 0.0) * (1.0 - 2.0 * TEXT_MARGIN)
    if w > 1.0 and abs(r.size.width.size.get() - w) > 0.5:
        r.size.width.size = w
    if abs(r.placement.position.x.get() - 0.5) > 1e-6:
        r.placement.position.x = 0.5
    active = t.activation.toString() == 'active'
    if msg is not None:
        if t.generator.text.get() != msg:
            t.generator.text.set(msg)
        if not active:
            t.activation.set(True)
    else:
        if active:
            t.activation.set(False)
        if t.generator.text.get() != '':
            t.generator.text.set('')

def rot_axis(a, ang):
    # rotation 3x3 d'angle ang autour de l'axe a (Rodrigues)
    a = unit(a, (0.0, 0.0, 1.0))
    c, s = math.cos(ang), math.sin(ang)
    K = [[0.0, -a[2], a[1]], [a[2], 0.0, -a[0]], [-a[1], a[0], 0.0]]
    return [[(c if i == j else 0.0) + (1.0 - c) * a[i] * a[j] + s * K[i][j] for j in range(3)] for i in range(3)]

def make_group(name):
    g = Oil.createObject('Group3dLayer')
    g.label = name
    set_color(g, COL_RIG)
    return g

def wrap_in_group(comp):
    # cree un Group3dLayer dans le conteneur du script et y deplace le script (copie ajoutee au groupe d'abord,
    # original retire ensuite : on ne perd jamais le script)
    grp = make_group(GROUP_NAME)
    cl = script.clone()
    dv = cl.dynamicVariables                             # la copie repart a zero : ni elements, ni rig, ni etat
    for i in range(len(dv)):
        nm = dv[i].getFriendlyName()
        if nm == 'Bones':
            while len(dv[i]):
                dv[i].removeAt(0)
        elif nm == 'Rig Data':
            dv[i].set('')
        elif nm in ('Create Rig', 'Setup Pivots'):
            dv[i].set(False)
    grp.tools.append(cl)
    comp.layers.append(grp)
    for i in range(len(comp.tools)):
        if comp.tools[i] is script:                      # (getUniqueIdentifier n'est pas convertible en Python)
            comp.tools.removeAt(i)
            break

def clear_bones(comp, N):
    # vide tous les emplacements de Bones (un WeakPointer ne se remet pas a None : on recree les emplacements) ; les
    # champs 'Bone n' des banks, lies aux anciens emplacements, sont retires (sync_banks les recree)
    while len(script.bones):
        script.bones.removeAt(0)
    for i in range(N):
        script.bones.append(Oil.createObject('WeakPointer(Layer)'))
    for i in range(len(comp.tools)):
        t = comp.tools[i]
        if t.getOilClassName() == 'ParameterBank' and tool_label(t) == SETUP_BANK:
            for j in range(len(t.parameters) - 1, -1, -1):
                if bone_param_index(str(t.parameters[j].label.get())):
                    t.parameters.removeAt(j)

def reset_script(comp, grp):
    # remise a zero : le rig (poignees, reglage des pivots, memoire) est supprime, les elements sont deverrouilles et
    # gardes tels quels, tous les parametres reprennent leur valeur par defaut et le script repasse en mode MANUEL
    # (Auto Rig decoche : il ne detecte plus rien tout seul, on remplit Bone 1..N puis on clique Create Rig)
    for i in range(len(script.bones)):
        e = script.bones[i].get()
        if e is not None:
            remove_deformers(e, json.loads(script.rigData.get()).get('prec0') if script.rigData.get() else None)
    if grp is not None:
        for i in range(len(grp.layers) - 1, -1, -1):
            nm = lab(grp.layers[i])
            if nm == TARGET_NAME or nm.startswith(NULL_PREFIX) or nm.startswith(SPHERE_PREFIX) or nm in LEGACY_NAMES:
                grp.layers.removeAt(i)
    script.rigData.set('')
    for k in ('last', 'chain', 'raw_prev', 'n', 'flips', 'hinge', 'flip'):
        S()[k] = None
    for vec in (script.jointLimits, script.jointFlips):
        for i in range(len(vec)):
            set_var(comp, vec[i], False)
    for var, val in ((script.enableIK, True), (script.setupPivots, False), (script.lockBones, True),
                     (script.planarMode, False), (script.fkMode, False), (script.reverseAxis, False),
                     (script.createRig, False), (script.showJoints, True), (script.boneCount, DEFAULT_BONES), (script.blendWidth, DEFAULT_BLEND),
                     (script.autoMode, False)):
        set_var(comp, var, val)
    set_var(comp, script.ik1Min, -math.pi)                  # pas de limite d'angle pour IK1
    set_var(comp, script.ik1Max, math.pi)
    script.jointDiameter.set(DEFAULT_DIAMETER)
    clear_bones(comp, 1)
    set_var(comp, script.resetRig, False)

def rig_candidates(grp):
    # elements 3D a rigger deja dans le groupe : calques de geometrie qui ne sont ni des poignees ni le texte
    out = []
    for i in range(len(grp.layers)):
        l = grp.layers[i]
        nm = lab(l)
        if l.getOilClassName() != 'GeometryLayer':
            continue
        if nm == TARGET_NAME or nm.startswith(NULL_PREFIX) or nm.startswith(SPHERE_PREFIX):
            continue
        out.append(l)
    return out

def make_icon_material(name):
    # materiau partage des poignees : rendu en surface (Side = Both, sans eclairage), composant Diffuse dont
    # la texture est une Compo transparente 1024 x 1024 contenant l'icone (croix a quatre fleches)
    mat = Oil.createObject('SurfaceGeometryRenderer')
    mat.label = name
    mat.side.set(2)
    mat.autoIlluminate.set(0.0)
    mat.depthBuffer.test.set(False)                      # poignees toujours dessinees par-dessus (face camera en 3D)
    while len(mat.components) > 1:                       # on ne garde que le composant Diffuse
        mat.components.removeAt(len(mat.components) - 1)
    comp = Oil.createObject('Compo')
    sl = Oil.createObject('ShapeLayer')
    sl.label = name
    gg = Oil.createObject('GroupShapeGenerator')
    for (bx, by, ex, ey) in ICON_SEGMENTS:
        ls = Oil.createObject('LineShapeGenerator')
        ls.segment.begin.x = bx; ls.segment.begin.y = by
        ls.segment.end.x = ex; ls.segment.end.y = ey
        gg.shapes.append(ls)
    sl.generator = gg
    sr = Oil.createObject('DefaultShapeRenderer')
    sr.fill.enabled = False
    sr.stroke.enabled = True
    sr.stroke.color.red.set(ICON_STROKE[0]); sr.stroke.color.green.set(ICON_STROKE[1])
    sr.stroke.color.blue.set(ICON_STROKE[2]); sr.stroke.color.alpha.set(1.0)
    sr.stroke.thickness = ICON_THICKNESS
    sl.renderer = sr
    comp.layers.append(sl)
    mat.components[0].map = comp
    return mat

def find_material(grp):
    # materiau ICON_NAME dans le MaterialBank du groupe (ou None)
    for i in range(len(grp.tools)):
        if grp.tools[i].getOilClassName() == 'MaterialBank':
            mb = grp.tools[i]
            for j in range(len(mb.materials)):
                if str(mb.materials[j].label.get()) == ICON_NAME:
                    return mb.materials[j]
    return None

def ensure_material(grp):
    # cree le MaterialBank et/ou le materiau de l'icone s'ils manquent ; True si quelque chose a ete cree
    mb = None
    for i in range(len(grp.tools)):
        if grp.tools[i].getOilClassName() == 'MaterialBank':
            mb = grp.tools[i]
    if mb is None:
        mb = Oil.createObject('MaterialBank')
        set_color(mb, COL_MATERIALS)
        mb.editable.set(False)                           # bank verrouille
        mb.materials.append(make_icon_material(ICON_NAME))
        grp.tools.append(mb)
        return True
    if find_material(grp) is None:
        mb.materials.append(make_icon_material(ICON_NAME))
        return True
    return False

def make_handle(name, p, size, mat):
    # poignee : plan a l'icone, rendu = REFERENCE vers le materiau partage (pointeur direct, location 1)
    g = Oil.createObject('GeometryLayer')
    g.label = name
    set_color(g, COL_RIG)
    gen = Oil.createObject('PlaneGeometryGenerator')
    gen.size.width = size
    gen.size.height = size
    g.generator = gen
    r = Oil.createObject('ReferenceGeometryLayerUser')
    ad = r.referencer.address
    ad.directPointer.set(mat)
    ad.location.set(1)
    g.renderer = r
    g.placement.orientation.x = -1.5707963                  # debout face a +Z (ajuste a chaque image, voir look_handles)
    g.placement.position.x = float(p[0]); g.placement.position.y = float(p[1]); g.placement.position.z = float(p[2])
    return g

def migrate_nulls(grp, mat, size):
    # anciens controleurs (NullLayer) -> poignees, positions conservees ; True si quelque chose a change
    idx, pts = [], []
    for i in range(len(grp.layers)):
        l = grp.layers[i]
        name = lab(l)
        if l.getOilClassName() == 'NullLayer' and (name == TARGET_NAME or name.startswith(NULL_PREFIX)):
            idx.append(i)
            pts.append((name, pos(l)))
    for i in reversed(idx):
        grp.layers.removeAt(i)
    for name, p in pts:
        grp.layers.append(make_handle(name, p, size, mat))
    return bool(idx)

def find_compo(el):
    # Compo qui contient l'element (porte la camera courante et la resolution) : on remonte les parents
    cur = el
    for _ in range(16):
        try:
            if cur.getOilClassName() == 'Compo':
                return cur
            cur = cur.parentElement
        except Exception:
            return None
        if cur is None:
            return None
    return None

def placement_rotation(pl):
    # rotation monde (3x3, colonnes = axes) d'un placement de camera, selon son type :
    # Matrix3dPlacement (matrice), PositionTargetUp3dPlacement (look-at, axe haut = Y), sinon orientation d'Euler
    # (TargetOrientationDistance / PositionOrientationSize / PositionOrientation : Rz Ry Rx, verifie par projection)
    cn = pl.getOilClassName()
    if cn == 'Matrix3dPlacement':
        m = pl.matrix
        cols = [unit((c.x.get(), c.y.get(), c.z.get()), d) for c, d in ((m.x, (1.0, 0.0, 0.0)), (m.y, (0.0, 1.0, 0.0)), (m.z, (0.0, 0.0, 1.0)))]
        return [[cols[0][0], cols[1][0], cols[2][0]], [cols[0][1], cols[1][1], cols[2][1]], [cols[0][2], cols[1][2], cols[2][2]]]
    if cn == 'PositionTargetUp3dPlacement':
        p, t = pl.position, pl.target
        back = unit(sub((p.x.get(), p.y.get(), p.z.get()), (t.x.get(), t.y.get(), t.z.get())), (0.0, 0.0, 1.0))   # la camera regarde vers -Z local
        right = unit(cross((0.0, 1.0, 0.0), back), (1.0, 0.0, 0.0))
        up = cross(back, right)
        return [[right[0], up[0], back[0]], [right[1], up[1], back[1]], [right[2], up[2], back[2]]]
    o = pl.orientation
    return euler_to_m(o.x.get(), o.y.get(), o.z.get())

def camera_rotation(root):
    # rotation de la camera de la Compo (courante, sinon par defaut) ; identite si illisible
    try:
        cam = root.currentCamera.get()
        if cam is None:
            cam = root.defaultCamera
        return placement_rotation(cam.placement)
    except Exception:
        return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

def look_handles(handles, comp, grp, planar, size, visible):
    # poignees : plans toujours a plat, paralleles a l'ecran de la camera de la Compo (2D comme 3D).
    # Taille = Joint Diameter ; visibles seulement si Show Joints (ou reglage des pivots)
    G = group_transform(grp)
    Rc = camera_rotation(comp)                      # camera de la Compo, en 2D comme en 3D
    Rl = mmul(mtr(G[4]), mmul(Rc, RX90))
    ex, ey, ez = m_to_euler(Rl)
    reload = S().get('reload')
    S()['reload'] = False
    for h in handles:
        if reload:
            h.renderer.referencer.reloadInstance.trig()        # la reference reprend l'etat actuel du materiau
        o = h.placement.orientation
        if abs(o.x.get() - ex) > 1e-6 or abs(o.y.get() - ey) > 1e-6 or abs(o.z.get() - ez) > 1e-6:
            o.x = ex; o.y = ey; o.z = ez
        s = h.generator.size
        if abs(s.width.get() - size) > 1e-6 or abs(s.height.get() - size) > 1e-6:
            s.width = size
            s.height = size
        if (h.activation.toString() == 'active') != visible:
            h.activation.set(visible)

# ---- FABRIK : J = N+1 points (racine, ..., pointe), Ls = N longueurs ----
def bend_offset(J):
    # (decalage perpendiculaire maximal des joints interieurs par rapport a la droite racine->pointe, vecteur)
    u = unit(sub(J[-1], J[0]), (1.0, 0.0, 0.0))
    best, bv = 0.0, (0.0, 0.0, 0.0)
    for i in range(1, len(J) - 1):
        o = perp(sub(J[i], J[0]), u)
        if norm(o) > best:
            best, bv = norm(o), o
    return best, bv

def fabrik(J, Ls, nref):
    N = len(Ls)
    S, T = J[0], J[-1]
    total = sum(Ls)
    v = sub(T, S)
    d = norm(v)
    u = unit(v, (1.0, 0.0, 0.0))
    if d >= total - 1e-6:
        out, c = [S], 0.0
        for L in Ls:
            c += L
            out.append(add(S, mul(u, c)))
        return out
    J = list(J)
    if N == 2:
        # 2 bones : formule exacte (loi des cosinus) ; cote du pli = celui de la pose courante
        L1, L2 = Ls
        d = max(abs(L1 - L2) + 1e-6, d)
        off, bv = bend_offset(J)
        n = unit(bv, unit(perp(nref, u), unit(cross(u, (0.0, 0.0, 1.0)), (0.0, 1.0, 0.0))))
        xa = (L1 * L1 + d * d - L2 * L2) / (2.0 * d)
        h = math.sqrt(max(0.0, L1 * L1 - xa * xa))
        E = add(S, add(mul(u, xa), mul(n, h)))
        return [S, E, add(S, mul(u, d))]
    if bend_offset(J)[0] < 1e-3 * total:
        # chaine droite : on la plie du cote memorise pour que FABRIK sache de quel cote aller
        nn = unit(perp(nref, u), unit(cross(u, (0.0, 0.0, 1.0)), (0.0, 1.0, 0.0)))
        c = 0.0
        for i in range(1, N):
            c += Ls[i - 1]
            t = c / total
            J[i] = add(add(S, mul(u, t * d)), mul(nn, math.sin(math.pi * t) * 0.05 * total))
    for _ in range(120):
        J[-1] = T
        for i in range(N - 1, -1, -1):
            J[i] = add(J[i + 1], mul(unit(sub(J[i], J[i + 1]), u), Ls[i]))
        J[0] = S
        for i in range(N):
            J[i + 1] = add(J[i], mul(unit(sub(J[i + 1], J[i]), u), Ls[i]))
        if norm(sub(J[-1], T)) < 1e-6:
            break
    return J

def rig_sig(els):
    # signature de la GEOMETRIE des bones (longueur, pivot, axe) : survit a un renommage des elements,
    # change si on remplace un element ou si on modifie sa taille / son ancrage
    parts = []
    for e in els:
        ax, ln, po, un = bone_axis(e)
        parts.append('%.4f,%.4f,%s' % (-1.0 if ln is None else ln, po, ','.join('%g' % v for v in ax)))
    return str(len(els)) + ':' + '|'.join(parts)

def rot_between(a, b):
    # rotation 3x3 minimale qui envoie le vecteur unitaire a sur b
    c = dot(a, b)
    v = cross(a, b)
    s = norm(v)
    if s < 1e-9:
        if c > 0:
            return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        ax = unit(cross(a, (1.0, 0.0, 0.0)), unit(cross(a, (0.0, 1.0, 0.0)), (0.0, 0.0, 1.0)))
        return [[2 * ax[i] * ax[j] - (1.0 if i == j else 0.0) for j in range(3)] for i in range(3)]
    k = mul(v, 1.0 / s)
    ang = math.atan2(s, c)
    ca, sa = math.cos(ang), math.sin(ang)
    K = [[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]]
    return [[(ca if i == j else 0.0) + (1.0 - ca) * k[i] * k[j] + sa * K[i][j] for j in range(3)] for i in range(3)]

def mat_vec(M, v):
    return (M[0][0]*v[0] + M[0][1]*v[1] + M[0][2]*v[2],
            M[1][0]*v[0] + M[1][1]*v[1] + M[1][2]*v[2],
            M[2][0]*v[0] + M[2][1]*v[1] + M[2][2]*v[2])

def fk_drag(chain, P, k, Ls, nref):
    # l'articulation k (1..N-1) a ete tiree vers P : les bones avant elle se reorientent pour l'atteindre
    # (longueurs fixes), tout ce qui est apres elle (articulations, pointe) suit comme un bloc rigide
    S = chain[0]
    if k == 1:
        u = unit(sub(P, S), unit(sub(chain[1], S), (1.0, 0.0, 0.0)))
        head = [S, add(S, mul(u, Ls[0]))]
    else:
        head = fabrik(list(chain[:k]) + [P], Ls[:k], nref)
    a = unit(sub(chain[k], chain[k - 1]), (1.0, 0.0, 0.0))
    b = unit(sub(head[k], head[k - 1]), a)
    Rm = rot_between(a, b)
    tail = [add(head[k], mat_vec(Rm, sub(chain[m], chain[k]))) for m in range(k + 1, len(chain))]
    return head + tail

def proj_ball(C, Q, Ls):
    # point le plus proche de Q atteignable par une chaine de longueurs Ls partant de C
    # (distance comprise entre la portee mini et la portee maxi de la chaine)
    total = sum(Ls)
    mn = max(0.0, 2.0 * max(Ls) - total)
    v = sub(Q, C)
    d = min(total, max(mn, norm(v)))
    return add(C, mul(unit(v, (1.0, 0.0, 0.0)), d))

def ik_pull(chain, P, k, Ls, nref):
    # mode IK : l'articulation k est tiree vers P, la racine et la pointe restent clouees. Q = point le
    # plus proche de P atteignable des deux cotes (projections alternees sur les deux zones
    # atteignables), puis chaque moitie de la chaine est resolue vers Q.
    N = len(Ls)
    S, T = chain[0], chain[-1]
    A, B = Ls[:k], Ls[k:][::-1]
    Q = P
    for _ in range(60):
        Qa = proj_ball(S, Q, A)
        Qb = proj_ball(T, Qa, B)
        if norm(sub(Qa, Qb)) < 1e-8:
            Q = Qb
            break
        Q = Qb
    if len(A) == 1:
        head = [S, add(S, mul(unit(sub(Q, S), (1.0, 0.0, 0.0)), A[0]))]
    else:
        head = fabrik(list(chain[:k]) + [Q], A, nref)
    seed = [T] + [chain[m] for m in range(N - 1, k, -1)] + [Q]
    if len(B) == 1:
        rev = [T, add(T, mul(unit(sub(Q, T), (1.0, 0.0, 0.0)), B[0]))]
    else:
        rev = fabrik(seed, B, nref)
    tail = list(reversed(rev))[1:]
    return head + tail

def limit_root_angle(J, Ls, lo, hi, nref):
    # angle de IK1 : direction du bone 1 dans le plan XY du rig (autour de Z, depuis l'axe X), limitee a [lo, hi]
    # (radians). Hors plage : le bone 1 est ramene sur la borne la plus proche, le reste de la chaine est resolu
    # depuis la nouvelle articulation 2 (la pointe n'atteint pas forcement la cible).
    if hi - lo >= 2.0 * math.pi - 1e-6 or (lo == 0.0 and hi == 0.0):
        return J
    d = sub(J[1], J[0])
    h = math.hypot(d[0], d[1])
    if h < 1e-9:
        return J
    a = math.atan2(d[1], d[0])
    if lo <= a <= hi:
        return J
    def gap(b):
        return abs(math.atan2(math.sin(a - b), math.cos(a - b)))
    b = lo if gap(lo) <= gap(hi) else hi
    nd = unit((h * math.cos(b), h * math.sin(b), d[2]), (1.0, 0.0, 0.0))
    J1 = add(J[0], mul(nd, Ls[0]))
    rest = fabrik([J1] + list(J[2:]), Ls[1:], nref)
    return [J[0]] + rest

def reflect_joint(P, A, B):
    # P tourne de 180 degres autour de la droite AB : memes distances a A et B, de l'autre cote
    u = unit(sub(B, A), (1.0, 0.0, 0.0))
    foot = add(A, mul(u, dot(sub(P, A), u)))
    return sub(mul(foot, 2.0), P)

def joint_turn(J, i):
    # produit vectoriel des directions des bones i et i+1 (axe et sinus du pli de l'articulation i+1)
    d0 = unit(sub(J[i + 1], J[i]), (1.0, 0.0, 0.0))
    d1 = unit(sub(J[i + 2], J[i + 1]), (1.0, 0.0, 0.0))
    return cross(d0, d1)

def init_hinges(J):
    # axe de charniere de chaque articulation : normale du pli actuel (sinon axe Z du rig, pli de la pose de depart)
    out = []
    for i in range(len(J) - 2):
        c = joint_turn(J, i)
        out.append(unit(c, (0.0, 0.0, -1.0)) if norm(c) > 0.05 else (0.0, 0.0, -1.0))
    return out

def enforce_limits(J, lim, hinge):
    # articulation limitee dont le pli est du mauvais cote de sa charniere : symetrique par rapport a ses voisines
    J = list(J)
    for _ in range(3):
        moved = False
        for i in range(len(lim)):
            if lim[i] and dot(joint_turn(J, i), hinge[i]) < -1e-6:
                J[i + 1] = reflect_joint(J[i + 1], J[i], J[i + 2])
                moved = True
        if not moved:
            break
    for i in range(len(hinge)):                 # la charniere suit le pli (balancement du plan) tant qu'il est net
        c = joint_turn(J, i)
        if norm(c) > 0.05:
            hinge[i] = unit(c, hinge[i])
    return J

def deform_info(obj):
    # geometrie de l'objet a deformer : (axe local, longueur, pivot po = distance de la BASE au calque le long de l'axe,
    # parametre de subdivision le long de l'axe, conteneur de precision ou None, connu ?). Mise a l'echelle du calque
    # incluse. Generateurs geres : Capsule, Cylinder (axe Y, base au calque), Box (plus grand cote, centree),
    # Plane (voir bone_axis), Rectangle, Sphere, Torus, Circle, Star (centres). Autres (Helix, Text, Particles,
    # maillages importes) : axe Y, 1 m, inconnu -> message d'avertissement.
    g = obj.generator
    sc = obj.placement.size
    sx, sy, sz = abs(sc.x.get()), abs(sc.y.get()), abs(sc.z.get())
    cn = g.getOilClassName()
    if cn == 'CapsuleGeometryGenerator':
        return (0.0, 1.0, 0.0), g.height.get() * sy, 0.0, g.heightPrecision, None, True
    if cn == 'CylinderGeometryGenerator':
        return (0.0, 1.0, 0.0), g.height.get() * sy, 0.0, g.precision.y, g.precision, True
    if cn == 'SphereGeometryGenerator':
        return (0.0, 1.0, 0.0), 2.0 * g.radius.get() * sy, g.radius.get() * sy, g.precision.y, g.precision, True
    if cn == 'BoxGeometryGenerator':
        dims = [g.size.x.get() * sx, g.size.y.get() * sy, g.size.z.get() * sz]
        k = dims.index(max(dims))
        ax = [0.0, 0.0, 0.0]
        ax[k] = 1.0
        return tuple(ax), dims[k], dims[k] * 0.5, (g.precision.x, g.precision.y, g.precision.z)[k], g.precision, True
    if cn == 'PlaneGeometryGenerator':
        ax, ln, po, un = bone_axis(obj)
        return ax, ln, po, (g.precision.x if ax[0] else g.precision.y), g.precision, True
    if cn == 'RectangleGeometryGenerator':
        w, h = g.size.width.get() * sx, g.size.height.get() * sy
        if w >= h:
            return (1.0, 0.0, 0.0), w, w * 0.5, g.precision, None, True
        return (0.0, 1.0, 0.0), h, h * 0.5, g.precision, None, True
    if cn == 'TorusGeometryGenerator':
        ln = 2.0 * (g.ringRadius.get() + g.thickness.get()) * sx
        return (1.0, 0.0, 0.0), ln, ln * 0.5, g.precision.x, g.precision, True
    if cn == 'CircleGeometryGenerator':
        return (1.0, 0.0, 0.0), 2.0 * g.radius.get() * sx, g.radius.get() * sx, g.precision, None, True
    if cn == 'StarGeometryGenerator':
        return (1.0, 0.0, 0.0), 2.0 * g.outerRadius.get() * sx, g.outerRadius.get() * sx, g.precision, None, True
    return (0.0, 1.0, 0.0), 1.0, 0.0, None, None, False

def object_axis(obj):
    # (base, axe, longueur) de l'objet dans le repere du groupe ; l'axe est tourne par l'orientation du calque
    p = obj.placement
    Rl = euler_to_m(p.orientation.x.get(), p.orientation.y.get(), p.orientation.z.get())
    ax, ln, po, pp, pc, known = deform_info(obj)
    axis = unit(mat_vec(Rl, ax), (0.0, 1.0, 0.0))
    return sub(pos(obj), mul(axis, po)), axis, max(ln, 1e-3)

def prec_state(obj):
    # etat a memoriser : [valeur de la precision de l'axe, precision uniforme (Precision2d / 3d) ou non]
    info = deform_info(obj)
    pp, pc = info[3], info[4]
    if pp is None:
        return None
    return [pp.get(), bool(pc.uniform.get()) if pc is not None and hasattr(pc, 'uniform') else False]

def prec_raise(obj):
    # assez de segments le long de l'axe pour que l'objet se plie ; si la precision est uniforme (plan, boite...), elle
    # est decouplee : seul l'axe de l'objet est subdivise
    info = deform_info(obj)
    pp, pc = info[3], info[4]
    if pp is None or pp.get() >= DEFORM_PRECISION:
        return
    if pc is not None and hasattr(pc, 'uniform') and pc.uniform.get():
        v = pc.x.get()
        pc.uniform.set(False)
        pc.x.set(v)
        pc.y.set(v)
        if hasattr(pc, 'z'):
            pc.z.set(v)
    pp.set(DEFORM_PRECISION)

def prec_restore(obj, st):
    info = deform_info(obj)
    pp, pc = info[3], info[4]
    if st is None or pp is None:
        return
    if not isinstance(st, list):                           # ancien format : juste la valeur
        st = [st, False]
    if pc is not None and hasattr(pc, 'uniform') and st[1]:
        pc.uniform.set(False)
        pc.x.set(int(st[0]))
        pc.y.set(int(st[0]))
        if hasattr(pc, 'z'):
            pc.z.set(int(st[0]))
        pc.uniform.set(True)
    else:
        pp.set(int(st[0]))

def remove_deformers(obj, prec0):
    # retire les modifiers IK_Deform_* de l'objet et remet sa precision d'origine
    try:
        mods = obj.generator.modifiers
        for i in range(len(mods) - 1, -1, -1):
            if str(mods[i].label.get()).startswith(DEFORM_PREFIX):
                mods.removeAt(i)
        prec_restore(obj, prec0)
    except Exception:
        pass

def ensure_deformers(obj, N):
    # N modifiers Transform3d IK_Deform_0..N-1 (le 0 sans masque : racine ; les autres avec un masque lineaire),
    # crees s'ils manquent ; la capsule recoit assez de segments pour se plier proprement
    gen = obj.generator
    prec_raise(obj)
    have = {}
    mods = gen.modifiers
    for i in range(len(mods) - 1, -1, -1):
        nm = str(mods[i].label.get())
        if nm.startswith(DEFORM_PREFIX):
            k = nm[len(DEFORM_PREFIX):]
            if k.isdigit() and int(k) < N and int(k) not in have:
                have[int(k)] = mods[i]
            else:
                mods.removeAt(i)
    for k in range(N):
        if k not in have:
            m = Oil.createObject('Transform3dGeometryModifier')
            m.label = DEFORM_PREFIX + str(k)
            if k > 0:
                m.masks.append(Oil.createObject('LinearGeometryMask'))
            mods.append(m)
    out = []
    for k in range(N):                                       # ordre : racine d'abord
        for i in range(len(mods)):
            if str(mods[i].label.get()) == DEFORM_PREFIX + str(k):
                out.append(mods[i])
                break
    return out

def put(param, v):
    # ecrit seulement si la valeur change (evite de reveiller la geometrie pour rien)
    if abs(param.get() - v) > 1e-6:
        param.set(float(v))

def deform_update(obj, data, J, blend):
    # modifiers selon la pose courante J (N+1 points, repere du groupe) et la pose de repos data['Rj'] :
    # T0 = rotation du bone 0 autour de la racine + translation de la racine ; Tk (k >= 1) = rotation relative du
    # bone k par rapport au bone k-1 autour de l'articulation COURANTE k, ponderee par un masque lineaire place sur le
    # bone k-1 deforme (de J_k - w a J_k + w) : chaine FK, les modifiers s'appliquent de la racine a la pointe
    N = len(J) - 1
    mods = ensure_deformers(obj, N)
    R = [tuple(r) for r in data['Rj']]
    p = obj.placement
    Rl = euler_to_m(p.orientation.x.get(), p.orientation.y.get(), p.orientation.z.get())
    Rt = mtr(Rl)
    P0 = pos(obj)
    def loc(q):                                              # point du groupe -> repere de l'objet
        return mat_vec(Rt, sub(q, P0))
    def locd(v):                                             # direction
        return mat_vec(Rt, v)
    d0 = [unit(sub(R[i + 1], R[i]), (0.0, 1.0, 0.0)) for i in range(N)]
    d1 = [unit(sub(J[i + 1], J[i]), (0.0, 1.0, 0.0)) for i in range(N)]
    A = [rot_between(d0[i], d1[i]) for i in range(N)]
    w = max(1e-3, min(blend * 0.5, 0.5 * min(data['Ls'])))
    for k in range(N):
        m = mods[k]
        if k == 0:
            W = A[0]
            anchor = loc(R[0])
            tr = locd(sub(J[0], R[0]))
        else:
            W = mmul(A[k], mtr(A[k - 1]))
            anchor = loc(J[k])
            tr = (0.0, 0.0, 0.0)
        Wl = mmul(Rt, mmul(W, Rl))                           # rotation exprimee dans le repere de l'objet
        ex, ey, ez = m_to_euler(Wl)
        put(m.anchor.x, anchor[0]); put(m.anchor.y, anchor[1]); put(m.anchor.z, anchor[2])
        put(m.rotation.x, ex); put(m.rotation.y, ey); put(m.rotation.z, ez)
        put(m.translation.x, tr[0]); put(m.translation.y, tr[1]); put(m.translation.z, tr[2])
        if k > 0 and len(m.masks):
            sg = m.masks[0].segment
            b = loc(sub(J[k], mul(d1[k - 1], w)))
            e = loc(add(J[k], mul(d1[k - 1], w)))
            put(sg.begin.x, b[0]); put(sg.begin.y, b[1]); put(sg.begin.z, b[2])
            put(sg.end.x, e[0]); put(sg.end.y, e[1]); put(sg.end.z, e[2])

def do_rig_deform(obj, jn, tgt, N):
    # points reguliers le long de l'axe de l'objet (repere du groupe) ; la chaine IK part de la pose de repos droite
    base, axis, H = object_axis(obj)
    Ls = [H / N] * N
    R = [add(base, mul(axis, H * i / N)) for i in range(N + 1)]
    for k in range(N):
        set_pos(jn[k], R[k])
    set_pos(tgt, R[N])
    nr = (1.0, 0.0, 0.0)                                      # le pli part a droite (axe X) par defaut
    S()['n'] = None
    S()['last'] = None
    S()['chain'] = None
    S()['flips'] = None
    S()['hinge'] = None
    for k in range(len(script.jointFlips)):
        set_var(script.parentElement, script.jointFlips[k], False)
    prec0 = prec_state(obj)
    old = script.rigData.get()
    if old:
        try:
            prec0 = json.loads(old).get('prec0', prec0)         # precision d'origine, pas celle deja augmentee
        except Exception:
            pass
    data = {'Rj': [list(r) for r in R], 'Ls': Ls, 'n': list(nr), 'flips': [False] * (N - 1), 'prec0': prec0}
    script.rigData.set(json.dumps(data))
    return data

def capture_rest(jn, tgt, nref, data):
    # fin du reglage des points : les poignees sont la nouvelle pose de repos (longueurs = distances entre poignees)
    N = len(jn)
    R = [pos(j) for j in jn] + [pos(tgt)]
    data['Rj'] = [list(r) for r in R]
    data['Ls'] = [max(1e-3, norm(sub(R[i + 1], R[i]))) for i in range(N)]
    data['setup'] = False
    off, bv = bend_offset(R)
    if off > 1e-3 * sum(data['Ls']):
        data['n'] = list(unit(bv, nref))
    S()['n'] = None
    S()['last'] = None
    S()['chain'] = None
    return data

def do_rig(els, jn, tgt):
    # assemble la chaine : longueurs = geometrie des bones ; depart = position (locale) de IK_Joint_1
    N = len(els)
    S0 = pos(jn[0])
    axes, Ls, Pos, Us = [], [], [], []
    for i, e in enumerate(els):
        ax, ln, po, un = bone_axis(e)
        axes.append(list(ax))
        if ln is None or ln < 1e-3:
            ln = norm(sub(pos(els[i + 1]), pos(e))) if i < N - 1 else 1.0
        Ls.append(ln if ln > 1e-3 else 1.0)
        Pos.append(po)
        Us.append(list(un) if un is not None else None)
    total = sum(Ls)
    nr = (0.0, 1.0, 0.0)
    d = 0.9 * total
    J, c = [S0], 0.0
    for i in range(1, N):
        c += Ls[i - 1]
        t = c / total
        J.append(add(add(S0, (t * d, 0.0, 0.0)), mul(nr, math.sin(math.pi * t) * 0.5 * total * 0.5)))
    J.append(add(S0, (d, 0.0, 0.0)))
    J = fabrik(J, Ls, nr)
    set_pos(tgt, J[-1])
    for k in range(1, N):
        set_pos(jn[k], J[k])
    S()['n'] = None
    S()['last'] = None
    S()['chain'] = None
    S()['flips'] = None
    S()['hinge'] = None
    for k in range(len(script.jointFlips)):      # le rig est recree dans sa pose de depart : Flip Bend decoches
        set_var(script.parentElement, script.jointFlips[k], False)
    data = {'gsig': rig_sig(els), 'Ls': Ls, 'E': axes, 'Po': Pos, 'U': Us, 'n': list(nr), 'flips': [False] * (N - 1)}
    script.rigData.set(json.dumps(data))
    return data

def capture_manual(els, jn, tgt, grp, LG, data, nref):
    # fin du reglage des pivots : les nulls sont les nouvelles articulations. Longueurs = distances entre
    # nulls ; chaque element est "colle" a son bone : on memorise sa position et sa rotation DANS le
    # repere du bone (O = decalage du pivot par rapport a l'articulation, Rr = rotation relative),
    # tels qu'il sont a cet instant. Marche pour toute geometrie / tout pivot.
    N = len(els)
    J = [pos(j) for j in jn] + [pos(tgt)]
    Ls = [max(1e-3, norm(sub(J[i + 1], J[i]))) for i in range(N)]
    dirs = [unit(sub(J[i + 1], J[i]), (1.0, 0.0, 0.0)) for i in range(N)]
    Fs = frames_for(dirs, nref)
    G = group_transform(grp)
    O, Rr = [], []
    for i, e in enumerate(els):
        if lab(e) in LG:
            Pl, Re = pos(e), get_rot(e)
        else:                                       # element hors du groupe : repasser dans le repere du groupe
            Pl = mat_vec(mtr(G[4]), sub(pos(e), G[3]))
            Re = mmul(mtr(G[4]), get_rot(e))
        O.append(list(mat_vec(mtr(Fs[i]), sub(Pl, J[i]))))
        Rr.append(flat(mmul(mtr(Fs[i]), Re)))
    data['Ls'], data['O'], data['Rr'], data['manual'], data['setup'] = Ls, O, Rr, True, False
    off, bv = bend_offset(J)
    if off > 1e-3 * sum(Ls):
        data['n'] = list(unit(bv, nref))
    S()['n'] = None
    S()['last'] = None
    S()['chain'] = None
    return data

def prune(vec, N, root_level, has_group):
    # retire d'un vecteur de layers : anciens controleurs et marqueurs (IK_Pole, IK_Sphere_n : remplaces par
    # les poignees), poignees en trop, et (au niveau Compo) tout ce qui est duplique maintenant que le
    # groupe IK_Rig existe
    idx = []
    for i in range(len(vec)):
        name = lab(vec[i])
        if name in LEGACY_NAMES or name.startswith(SPHERE_PREFIX):
            idx.append(i)
        if root_level and has_group and (name == TARGET_NAME or name.startswith(NULL_PREFIX)):
            idx.append(i)
        if name.startswith(NULL_PREFIX):
            k = name[len(NULL_PREFIX):]
            if (not k.isdigit()) or int(k) > N:
                idx.append(i)
    for i in sorted(set(idx), reverse=True):
        vec.removeAt(i)

def main():
    # conteneur du script : un Group3dLayer (le groupe EST le rig : bones, poignees, texte, bank de materiau, banks
    # de parametres y vivent ; il peut etre imbrique dans un autre rig) ou, ancien montage, une Compo (le rig est
    # alors cree dans un sous-groupe IK_Rig)
    comp = script.parentElement
    group_mode = comp.getOilClassName() == 'Group3dLayer'
    if not group_mode and not any(lab(comp.layers[i]) == GROUP_NAME and comp.layers[i].getOilClassName() == 'Group3dLayer'
                                  for i in range(len(comp.layers))):
        # script lance hors d'un groupe 3D : on cree le groupe et on y met le script, AVANT de creer banks et materiaux
        wrap_in_group(comp)
        return 'IK_Deform : script place dans un nouveau groupe 3D'
    root = find_compo(comp)                                  # Compo ancetre : camera courante, resolution

    # nombre de bones -> nombre d'emplacements
    N = max(MIN_BONES, min(MAX_BONES, int(script.boneCount.get())))
    while len(script.bones) < 1:                             # un seul emplacement : l'objet a deformer
        script.bones.append(Oil.createObject('WeakPointer(Layer)'))
    while len(script.bones) > 1:
        script.bones.removeAt(len(script.bones) - 1)
    for vec in (script.jointLimits, script.jointFlips):      # un booleen par articulation (entre deux bones) : N - 1
        while len(vec) < N - 1:
            vec.append(Oil.createObject('Boolean'))
        while len(vec) > N - 1:
            vec.removeAt(len(vec) - 1)

    if script.ik1Min.get() == 0.0 and script.ik1Max.get() == 0.0:    # jamais regles : plage complete (pas de limite)
        set_var(comp, script.ik1Min, -math.pi)
        set_var(comp, script.ik1Max, math.pi)
    have_banks = set(tool_label(comp.tools[i]) for i in range(len(comp.tools)))
    if S().get('import_ver') != IMPORT_VERSION or not all(n in have_banks for n in BANK_NAMES):
        # a l'import du script dans un projet, et a chaque image tant qu'un bank manque
        try:
            ensure_banks(comp, N)                            # cree les 2 banks et leurs parametres lies s'ils manquent
            set_color(script, COL_SCRIPT)                    # couleur du script lui-meme
            S()['import_ver'] = IMPORT_VERSION
            S().pop('bank_err', None)
        except Exception as e:
            if S().get('bank_err') != str(e):                # erreur visible dans la console, une seule fois
                print('IK Rig : creation des banks impossible : %r' % (e,))
            S()['bank_err'] = str(e)
            S()['import_ver'] = IMPORT_VERSION               # pas de nouvel essai a chaque image
    try:
        sync_banks(comp, N)                                  # Bone 1..N, Limit 180 et Flip Bend : suivent Bone Count
        mirror_bones(comp, N)
    except Exception as e:
        if S().get('bone_err') != str(e):
            print('IK Rig : champs Bone impossibles : %r' % (e,))
        S()['bone_err'] = str(e)

    # groupe IK_Rig
    grp = comp if group_mode else None
    if not group_mode:
        for i in range(len(comp.layers)):
            if lab(comp.layers[i]) == GROUP_NAME and comp.layers[i].getOilClassName() == 'Group3dLayer':
                grp = comp.layers[i]
    show = script.showJoints.get()
    size = max(0.001, script.jointDiameter.get())          # taille des poignees (cote du plan)
    if not group_mode:
        prune(comp.layers, N, True, grp is not None)
    LG = {}
    mat = None
    if grp is not None:
        prune(grp.layers, N, False, True)
        if ensure_material(grp):                           # MaterialBank + materiau de l'icone (crees s'ils manquent)
            return 'IK_Deform : creation du materiau des poignees...'
        for i in range(len(grp.tools)):
            if grp.tools[i].getOilClassName() == 'MaterialBank':
                set_lock(grp.tools[i], True)               # le MaterialBank est toujours verrouille
        mat = find_material(grp)
        if mat.depthBuffer.test.get():                     # materiau cree a la main : test de profondeur coupe, puis
            mat.depthBuffer.test.set(False)                # les references existantes sont rechargees (voir look_handles)
            S()['reload'] = True
        if migrate_nulls(grp, mat, size):                  # anciens nulls -> poignees (positions conservees)
            return 'IK_Deform : migration des controleurs en poignees...'
        for i in range(len(grp.layers)):
            LG[lab(grp.layers[i])] = grp.layers[i]
        if INFO_NAME not in LG:                  # adopte un calque texte sans nom deja present dans le groupe
            for i in range(len(grp.layers)):
                l = grp.layers[i]
                if l.getOilClassName() == 'TextLayer' and lab(l) == '':
                    l.label = INFO_NAME
                    LG[INFO_NAME] = l
                    break
        _frame['layer'] = LG.get(INFO_NAME)
        _frame['width'] = root.rasterizer.resolution.width.get() if root is not None else 0.0   # largeur de la compo (px)
        if S().get('col_ver') != IMPORT_VERSION:             # une fois a l'import : couleurs du code couleur
            if INFO_NAME in LG:
                set_color(LG[INFO_NAME], COL_MATERIALS)
                style_text(LG[INFO_NAME])
            for nm, l in LG.items():
                if (nm == TARGET_NAME or nm.startswith(NULL_PREFIX)) and l.getOilClassName() == 'GeometryLayer':
                    set_color(l, COL_RIG)
            S()['col_ver'] = IMPORT_VERSION

    if script.resetRig.get():                        # bouton RESET
        reset_script(comp, grp)
        return 'IK_Deform : remise a zero (mode manuel)'

    if grp is not None and INFO_NAME not in LG:      # texte d'info : cree des le depart (message d'accueil)
        grp.layers.append(make_text(INFO_NAME))
        return 'IK_Deform : creation du texte d\'info...'

    # rig pas encore cree : les elements a rigger sont ceux QUI SONT DANS LE GROUPE. Un emplacement qui designe un
    # element hors du groupe est vide ; emplacements vides = on detecte les elements du groupe, on adapte Bone Count,
    # on les range dans Bone 1..N et on lance Create Rig ; emplacements tous remplis = on lance Create Rig ;
    # sinon message "glissez les elements 3D dans le groupe"
    no_rig = not script.rigData.get() or TARGET_NAME not in LG or any((NULL_PREFIX + str(i + 1)) not in LG for i in range(N))
    if grp is not None and no_rig:                  # pas de rig : rien de memorise, ou poignees absentes du groupe
        cands = rig_candidates(grp)
        slots = [script.bones[0].get()]
        auto = script.autoMode.get()                # Auto Rig decoche = mode manuel : rien n'est detecte tout seul
        if auto and any(e is not None and not any(e is c for c in cands) for e in slots):
            clear_bones(comp, 1)
            script.rigData.set('')
            return 'IK_Deform : elements hors du groupe, emplacements vides'
        if auto and all(e is None for e in slots):
            if len(cands) < 1:
                _frame['msgs'].append(MSG_DRAG)
                return 'IK_Deform : glisser l\'objet 3D dans le groupe'
            set_var(comp, script.bones[0], cands[0])
            set_var(comp, script.createRig, True)
            return 'IK_Deform : objet detecte, creation du rig'
        if auto and all(e is not None for e in slots) and not script.createRig.get():
            set_var(comp, script.createRig, True)        # emplacements remplis a la main : le rig se cree tout seul
            return 'IK_Deform : creation du rig'

    obj = script.bones[0].get()
    els = [obj]
    if obj is None:
        _frame['msgs'].append(MSG_DROP)
        return 'IK_Deform : deposer l\'objet 3D dans Object'
    if not deform_info(obj)[5]:
        _frame['msgs'].append(MSG_UNKNOWN % obj.generator.getOilClassName().replace('GeometryGenerator', ''))
    tgt = LG.get(TARGET_NAME)
    jn = [LG.get(NULL_PREFIX + str(i + 1)) for i in range(N)]

    # bouton Create Rig (reste coche jusqu'a la fin : les objets crees sont retrouves a l'image suivante)
    if script.createRig.get():
        if grp is None:
            comp.layers.append(make_group(GROUP_NAME))
            return 'IK_Deform : creation du groupe IK_Rig...'
        created = False
        for i in range(N):
            if jn[i] is None:
                grp.layers.append(make_handle(NULL_PREFIX + str(i + 1), pos(obj), size, mat))
                created = True
        if tgt is None:
            grp.layers.append(make_handle(TARGET_NAME, pos(obj), size, mat))
            created = True
        if INFO_NAME not in LG:
            grp.layers.append(make_text(INFO_NAME))
            created = True
        if created:
            return 'IK_Deform : creation des controleurs...'
        do_rig_deform(obj, jn, tgt, N)
        ensure_deformers(obj, N)
        set_var(comp, script.createRig, False)
        return 'IK_Deform : rig cree'

    raw = script.rigData.get()
    data = json.loads(raw) if raw else None
    if data is None or 'Rj' not in data or len(data.get('Ls', [])) != N:
        _frame['msgs'].append(MSG_RIG)
        return 'IK_Deform : cliquer Create Rig'
    if grp is None or tgt is None or any(j is None for j in jn):
        _frame['msgs'].append(MSG_RIG)
        return 'IK_Deform : controleurs introuvables, cliquer Create Rig'

    in_setup = script.setupPivots.get()

    # poignees : face camera, taille, visibilite (Show Joints ; toujours visibles pendant Setup Pivots) ;
    # tant qu'elles sont visibles, un texte previent de les masquer avant le rendu
    planar = script.planarMode.get()
    look_handles(jn + [tgt], root, grp, planar, size, show or in_setup)
    if show:
        _frame['msgs'].append(MSG_JOINTS)
    # Setup Pivots : le rig est fige, les nulls se deplacent librement (ex. sur les trous des textures) ;
    # a la sortie, les nulls deviennent les nouvelles articulations (capture_manual)
    nref0 = S().get('n') or tuple(data.get('n', (0.0, 1.0, 0.0)))
    if script.setupPivots.get():
        if not data.get('setup'):
            data['setup'] = True
            script.rigData.set(json.dumps(data))
        S()['last'] = None
        S()['chain'] = None
        _frame['msgs'].append(MSG_SETUP)
        deform_update(obj, data, list(data['Rj']), script.blendWidth.get())     # pendant le reglage : objet au repos
        return 'IK_Deform : reglage des points (deplacer les poignees, puis decocher)'
    if data.get('setup'):
        data = capture_rest(jn, tgt, nref0, data)
        script.rigData.set(json.dumps(data))
    if not script.enableIK.get():
        S()['last'] = None
        S()['raw_prev'] = None
        _frame['msgs'].append(MSG_IK_OFF)
        return 'IK_Deform : IK desactive'

    # pose courante de la chaine (repere du groupe) = positions des poignees (+ pointe = cible)
    raw = [pos(j) for j in jn] + [pos(tgt)]
    J = list(raw)
    nref = S().get('n') or tuple(data.get('n', (0.0, 1.0, 0.0)))
    if planar:
        z0 = J[0][2]
        J = [(p[0], p[1], z0) for p in J]
        nref = unit((nref[0], nref[1], 0.0), (0.0, 1.0, 0.0))
        if abs(pos(tgt)[2] - z0) > 1e-9:
            set_pos(tgt, J[-1])

    # une articulation intermediaire a ete tiree a la main (position differente de celle ecrite a
    # l'image precedente, racine et cible immobiles) : mode FK, les suivantes + la cible suivent
    last, chain = S().get('last'), S().get('chain')
    if last is not None and chain is not None and len(last) == N + 1 and len(chain) == N + 1:
        mv = [norm(sub(raw[i], last[i])) for i in range(N + 1)]
        k = max(range(1, N), key=lambda i: mv[i])
        # un vrai tirage a la main CHANGE a chaque image ; une valeur reecrite a l'identique par la timeline
        # (poignee animee, y compris tenue apres la derniere cle) ne change pas : ce n'est pas un tirage
        rawprev = S().get('raw_prev')
        changed = rawprev is None or len(rawprev) != N + 1 or norm(sub(raw[k], rawprev[k])) > 1e-5
        if mv[k] > 1e-5 and mv[0] <= 1e-5 and mv[N] <= 1e-5 and changed:
            if script.fkMode.get():
                J = fk_drag(chain, J[k], k, data['Ls'], nref)       # FK : la suite et la cible suivent
                set_pos(tgt, J[-1])
            else:
                J = ik_pull(chain, J[k], k, data['Ls'], nref)       # IK : la pointe reste sur la cible
    # Flip Bend n = ETAT (case coche / decoche), un par articulation : a chaque changement d'etat, l'articulation n
    # passe de l'autre cote de la droite formee par ses deux voisines (symetrie). Etat precedent memorise (rigData).
    nj = N - 1
    flips_now = [bool(script.jointFlips[i].get()) for i in range(nj)]
    flips_prev = S().get('flips')
    if flips_prev is None or len(flips_prev) != nj:
        fp = data.get('flips')
        flips_prev = list(fp) if fp is not None and len(fp) == nj else list(flips_now)
    hinge = S().get('hinge')                    # axe de charniere de chaque articulation (sens autorise du pli)
    if hinge is None or len(hinge) != nj:
        hinge = init_hinges(J)
    flipped = False
    for i in range(nj):
        if flips_now[i] != flips_prev[i]:
            J[i + 1] = reflect_joint(J[i + 1], J[i], J[i + 2])
            hinge[i] = mul(hinge[i], -1.0)
            flipped = True
    if flipped:
        off, bv = bend_offset(J)
        nref = unit(bv, nref) if off > 1e-3 * sum(data['Ls']) else mul(nref, -1.0)
        S()['n'] = nref
    S()['flips'] = flips_now
    if data.get('flips') != flips_now:
        data['flips'] = flips_now
        script.rigData.set(json.dumps(data))
    J = fabrik(J, data['Ls'], nref)
    if planar:
        J = [(p[0], p[1], J[0][2]) for p in J]
    # Limit 180 : une articulation limitee ne peut plier que d'un seul cote (180 degres au lieu de 360)
    J = enforce_limits(J, [bool(script.jointLimits[i].get()) for i in range(nj)], hinge)
    S()['hinge'] = hinge
    J = limit_root_angle(J, data['Ls'], script.ik1Min.get(), script.ik1Max.get(), nref)   # angle min / max de IK1

    # memoriser le cote du pli (direction du plus grand decalage), pour ne pas sauter quand la chaine se tend
    off, bv = bend_offset(J)
    if off > 1e-3 * sum(data['Ls']):
        nref = unit(bv, nref)
        S()['n'] = nref

    # deformation de l'objet selon la pose courante ; les poignees intermediaires suivent la chaine resolue
    deform_update(obj, data, J, script.blendWidth.get())
    for i in range(1, N):
        set_pos(jn[i], J[i])
    # memoriser : chaine resolue + positions des poignees telles que stockees (detection du tirage a la main)
    S()['chain'] = J
    S()['last'] = [pos(jn[0])] + [pos(jn[i]) for i in range(1, N)] + [pos(tgt)]
    S()['raw_prev'] = raw           # positions lues cette image (avant nos ecritures)
    return 'IK_Deform'

try:
    msg = main()
except Exception as ex:
    msg = 'IK_Deform ERR: ' + str(ex)
try:
    apply_info()
except Exception as ex:
    msg = 'IK_Deform ERR (info): ' + str(ex)
if S().get('last_label') != msg:
    script.label = msg
    S()['last_label'] = msg
