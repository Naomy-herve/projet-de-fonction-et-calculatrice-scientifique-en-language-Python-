#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXUS//CALC — Scientific Function Workspace
===========================================
Application Python de calcul et d'analyse de fonctions, avec interface Tkinter.
Matplotlib et NumPy sont facultatifs mais recommandés pour le tracé interactif.

Installation recommandée :  python -m pip install matplotlib numpy
Lancement :                 python main.py

Fonctionnalités conservées de la version web :
  • En-tête (logo, navigation WORKSPACE / METHODS / NOTES / ABOUT, GUIDE)
  • Section hero + pastilles
  • Panneau « INPUT PARAMETERS » : type de fonction, a, b, c, x₀, WINDOW,
    aperçu f(x) en direct, boutons CALCULATE / UPDATE et RESET WORKSPACE
  • Panneau « ANALYSIS / OUTPUT » avec 8 onglets :
    Overview, Domain, Limits, Variations, Roots, Points, Tangent, Graph
  • Calculs de fonctions (discriminant, racines, sommet, f(x₀), pente, dérivée…)
  • Onglet « Scientific Calculator » : opérations, trigonométrie, logarithmes,
    exponentielles, racines, constantes π/e, factorial et saisie au clavier.
  • Interface inspirée par le caractère visuel affirmé de Preymaker : grand titre,
    grille discrète, contrastes forts, panneaux sombres et accent vert lumineux.
  • Code organisé par sections commentées : thème, moteur mathématique, composants,
    widgets, onglets, mise en page et point d'entrée.
  • Sans Matplotlib, le tracé de secours Canvas reste disponible.
"""

import ast  # Analyse syntaxique ampiasain mba isecuriséna n'ilay calculatrice 
import math 
import re  
import sys #module systeme mb afahna manokatra ireo fichier
import tkinter as tk  # module tkinter miandraikitra ny interface 
from decimal import Decimal 
from tkinter import font as tkfont
from tkinter import ttk

# Matplotlib miandraikitra ny graphique izn hoe ilay courbe 
try:
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    np = None
    Figure = FigureCanvasTkAgg = NavigationToolbar2Tk = None
    MATPLOTLIB_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════════════
#  Palette ty ny pallete miandraikitr ny interface trasparence ,
# eo ihan kou ny centralisaytion des couleur 
# ════════════════════════════════════════════════════════════════════════════


def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def blend(fg, bg, a):
    """Couleur `fg` d'opacité `a` posée sur `bg`."""
    f, b = _rgb(fg), _rgb(bg)
    return '#%02x%02x%02x' % tuple(round(f[i] * a + b[i] * (1 - a)) for i in range(3))


def wa(a, base):
    """Blanc d'opacité `a` posé sur `base` (équivalent de white/NN)."""
    return blend('#ffffff', base, a)


BG = '#07101b'
FG = '#f4f7fb'
LIME = '#b8ff35'
HEADER_BG = blend('#081522', BG, .80)
ASIDE_BG = blend('#0b1a29', BG, .90)
OUT_BG = blend('#091624', BG, .80)
PREVIEW_BG = '#0d2031'
SELECT_BG = '#101f2e'
GRAPH_BG = '#07131f'
NOTE_BG = blend(LIME, OUT_BG, .06)
NOTE_BORDER = blend(LIME, OUT_BG, .30)

TABS = ['Overview', 'Domain', 'Limits', 'Variations', 'Roots', 'Points', 'Tangent', 'Graph', 'Scientific Calculator']
FUNCTIONS = ['Quadratic', 'Affine', 'Power', 'Exponential', 'Logarithm']
NAV_ITEMS = ['WORKSPACE', 'METHODS', 'NOTES', 'ABOUT']

# ════════════════════════════════════════════════════════════════════════════
#  Calculatrice scientifique : 
# ity section de code ty no miandraikitr ny 
# fonctionnement et creation de moteur de calculatrice scientifique 
# le module AST manao ny controle ny calcule , bloquer ireo calcule impossible ,
# izy ihan kou no miandraikitr ny message d'erreur (mamadika ireo phrase d'erreur hoe comprehensible, mazava )
# Marihina fa ny champ de calcul tsy afak miexecuter code de construction python 
SCIENTIFIC_FUNCTIONS = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'sqrt': math.sqrt, 'log': math.log10, 'ln': math.log,
    'log2': math.log2, 'exp': math.exp, 'abs': abs,
    'floor': math.floor, 'ceil': math.ceil, 'factorial': math.factorial,
    'degrees': math.degrees, 'radians': math.radians,
}
SCIENTIFIC_CONSTANTS = {'pi': math.pi, 'e': math.e, 'tau': math.tau}
_ALLOWED_AST = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name,
                ast.Load, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div,
                ast.FloorDiv, ast.Mod, ast.Pow, ast.UAdd, ast.USub)


def scientific_eval(expression):
    """
    Évalue une expression mathématique à partir d'une liste blanche.
    Les seules opérations possibles sont les opérateurs arithmétiques simples
    et les fonctions/constantes de SCIENTIFIC_FUNCTIONS et SCIENTIFIC_CONSTANTS.
    Les attributs, indexations, compréhensions, affectations et noms inconnus
    sont refusés avant l'évaluation, sans accès aux fonctions intégrées Python.
    Des limites de taille et de complexité réduisent les risques de calcul excessif.
    Les erreurs de domaine ou de syntaxe sont remontées à l'interface pour affichage.
    """
    expression = expression.strip().replace('×', '*').replace('÷', '/').replace('−', '-')
    expression = expression.replace('π', 'pi').replace('√(', 'sqrt(').replace('^', '**')
    if not expression:
        raise ValueError('Saisissez une expression à calculer.')
    if len(expression) > 240:
        raise ValueError("Expression trop longue (240 caractères maximum).")
    try:
        tree = ast.parse(expression, mode='eval')
    except (SyntaxError, ValueError) as exc:
        raise ValueError("Syntaxe invalide. Vérifiez les parenthèses et les opérateurs.") from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > 100:
        raise ValueError("Expression trop complexe.")
    for node in nodes:
        if not isinstance(node, _ALLOWED_AST):
            raise ValueError('Expression non autorisée.')
        if isinstance(node, ast.Constant) and (isinstance(node.value, bool) or
                                                not isinstance(node.value, (int, float))):
            raise ValueError('Seuls les nombres sont autorisés.')
        if isinstance(node, ast.Name) and node.id not in SCIENTIFIC_FUNCTIONS and node.id not in SCIENTIFIC_CONSTANTS:
            raise ValueError('Fonction ou constante inconnue : ' + node.id)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in SCIENTIFIC_FUNCTIONS:
                raise ValueError('Cette fonction n’est pas disponible.')
            if node.keywords:
                raise ValueError("Les arguments nommés ne sont pas autorisés.")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if isinstance(node.right, ast.Constant) and isinstance(node.right.value, (int, float)):
                if abs(node.right.value) > 1000:
                    raise ValueError("Exposant trop grand (valeur absolue maximale : 1000).")
    # Évaluation récursive :mifanohitr @ eval(), izan hoe isaky ny operation atao controlena manokana
    # ohatr : ilan @ calcul trop long , limite ,factoriel trop grand 
    binary_ops = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
        ast.FloorDiv: lambda left, right: left // right,
        ast.Mod: lambda left, right: left % right,
    }

    def checked(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Le résultat doit être un nombre réel.')
        try:
            if not math.isfinite(float(value)):
                raise ValueError('Le résultat est infini ou indéfini.')
        except OverflowError as exc:
            raise ValueError('Résultat trop grand pour être représenté.') from exc
        return value

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant):
            return checked(node.value)
        if isinstance(node, ast.Name):
            if node.id in SCIENTIFIC_CONSTANTS:
                return SCIENTIFIC_CONSTANTS[node.id]
            if node.id in SCIENTIFIC_FUNCTIONS:
                return SCIENTIFIC_FUNCTIONS[node.id]
            raise ValueError('Fonction ou constante inconnue : ' + node.id)
        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            if isinstance(node.op, ast.UAdd):
                return checked(+value)
            if isinstance(node.op, ast.USub):
                return checked(-value)
        if isinstance(node, ast.BinOp):
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow):
                if abs(float(right)) > 1000:
                    raise ValueError('Exposant trop grand (valeur absolue maximale : 1000).')
                # math.pow refuse les résultats complexes et lève une erreur en cas de dépassement.
                return checked(math.pow(float(left), float(right)))
            operation = binary_ops.get(type(node.op))
            if operation is not None:
                return checked(operation(left, right))
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in SCIENTIFIC_FUNCTIONS:
                raise ValueError('Cette fonction n’est pas disponible.')
            if node.keywords:
                raise ValueError('Les arguments nommés ne sont pas autorisés.')
            args = [evaluate(arg) for arg in node.args]
            if node.func.id == 'factorial':
                if len(args) != 1 or not isinstance(args[0], int) or not 0 <= args[0] <= 170:
                    raise ValueError('factorial() accepte un entier de 0 à 170.')
            result = SCIENTIFIC_FUNCTIONS[node.func.id](*args)
            return checked(result)
        raise ValueError('Expression non autorisée.')

    try:
        result = evaluate(tree)
        numeric = float(result)
    except (OverflowError, ZeroDivisionError, ValueError, TypeError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith((
                'Expression', 'Fonction', 'Cette fonction', 'Les arguments', 'factorial',
                'Exposant', 'Le résultat', 'Résultat')):
            raise
        raise ValueError('Calcul impossible : vérifiez le domaine mathématique.') from exc
    if not math.isfinite(numeric):
        raise ValueError('Le résultat est infini ou indéfini.')
    return format_number(numeric)


# ════════════════════════════════════════════════════════════════════════════
#  Logique mathématique et analyse des fonctions
# Les conversions numériques acceptent les valeurs usuelles saisies dans les champs.
# Les fonctions de calcul sont indépendantes de Tkinter afin de pouvoir être testées.
# Chaque type de fonction possède ses propres règles de domaine et de dérivation.
# Les valeurs non définies sont représentées par NaN plutôt que de faire planter l'UI.
# Les lignes d'analyse doivent décrire le type réellement sélectionné, pas seulement un polynôme.
# ════════════════════════════════════════════════════════════════════════════

_NUM_RE = re.compile(r'^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$')
_HEX_RE = re.compile(r'^0[xX][0-9a-fA-F]+$')


def js_number(s):
    """Équivalent de Number(s) en JavaScript (NaN si invalide)."""
    s = s.strip()
    if s == '':
        return 0.0
    if s in ('Infinity', '+Infinity'):
        return math.inf
    if s == '-Infinity':
        return -math.inf
    if _HEX_RE.match(s):
        return float(int(s, 16))
    if _NUM_RE.match(s):
        return float(s)
    return math.nan


def num(s):
    """Équivalent de `Number(s) || 0`."""
    v = js_number(s)
    return 0.0 if (math.isnan(v) or v == 0) else v


def js_str(v):
    """Équivalent de String(number) en JavaScript."""
    if math.isnan(v):
        return 'NaN'
    if math.isinf(v):
        return 'Infinity' if v > 0 else '-Infinity'
    if v == int(v) and abs(v) < 1e21:
        return str(int(v))
    r = repr(v)
    if 'e' in r or 'E' in r:
        if abs(v) >= 1e-6 and abs(v) < 1e21:
            return format(Decimal(r), 'f')
        return re.sub(r'e([+-])0*(\d)', r'e\1\2', r)
    return r


def format_number(v):
    """formatNumber() de l'application d'origine."""
    if not math.isfinite(v):
        return 'undefined'
    if v == int(v):
        return js_str(v)
    s = '%.4f' % v
    s = re.sub(r'0+$', '', s)
    s = re.sub(r'\.$', '', s)
    return s


def sign(v):
    """'+' si v >= 0, sinon '−' (NaN → '−', comme en JS)."""
    return '+' if v >= 0 else '−'


def _safe_function_value(ftype, x, a, b, c):
    """Évalue l'une des cinq fonctions proposées, en signalant les domaines invalides."""
    try:
        if ftype == 'Quadratic':
            y = a * x * x + b * x + c
        elif ftype == 'Affine':
            y = a * x + b
        elif ftype == 'Power':
            y = x ** a
        elif ftype == 'Exponential':
            y = a ** x
        elif ftype == 'Logarithm':
            if x <= 0 or a <= 0 or a == 1:
                return math.nan
            y = math.log(x, a)
        else:
            return math.nan
        return float(y) if math.isfinite(float(y)) else math.nan
    except (ValueError, OverflowError, ZeroDivisionError, TypeError):
        return math.nan


def compute_values(a, b, c, x0, ftype='Quadratic'):
    """
    Calcule les indicateurs de l'onglet d'analyse pour le type de fonction choisi.
    Les champs a, b, c gardent leur sens pour les fonctions quadratiques et affines.
    Pour Power, a est l'exposant ; pour Exponential, a est la base ; pour Logarithm,
    a est la base du logarithme. Les valeurs hors domaine deviennent NaN et
    l'interface peut les afficher sans faire planter toute l'application.
    Les clés historiques sont conservées afin de rester compatibles avec les widgets.
    """
    av, bv, cv, x0v = num(a), num(b), num(c), num(x0)
    discriminant = bv * bv - 4 * av * cv
    roots = []
    vertex_x, vertex_y = 0.0, 0.0
    if ftype == 'Quadratic':
        if av != 0 and discriminant >= 0 and math.isfinite(discriminant):
            root_delta = math.sqrt(discriminant)
            roots = sorted([(-bv - root_delta) / (2 * av), (-bv + root_delta) / (2 * av)])
        elif av == 0 and bv != 0:
            roots = [-cv / bv]
        vertex_x = 0.0 if av == 0 else -bv / (2 * av)
        vertex_y = _safe_function_value(ftype, vertex_x, av, bv, cv)
        slope = 2 * av * x0v + bv
    elif ftype == 'Affine':
        discriminant = math.nan
        # f(x)=a·x+b : si a=0, la fonction est constante (aucune racine sauf 0=0).
        roots = [-bv / av] if av != 0 else []
        vertex_x, vertex_y, slope = 0.0, bv, av
    elif ftype == 'Power':
        discriminant = math.nan
        roots = [0.0] if av > 0 else []
        vertex_x = 0.0
        vertex_y = _safe_function_value(ftype, vertex_x, av, bv, cv)
        if av == 0:
            slope = 0.0
        elif x0v != 0 or av >= 1:
            try:
                slope = av * (x0v ** (av - 1))
                if not math.isfinite(float(slope)):
                    slope = math.nan
            except (ValueError, OverflowError, ZeroDivisionError, TypeError):
                slope = math.nan
        else:
            slope = math.nan
    elif ftype == 'Exponential':
        discriminant = math.nan
        roots = []  # Une exponentielle de base positive différente de 1 ne s'annule pas.
        vertex_x, vertex_y = 0.0, _safe_function_value(ftype, 0.0, av, bv, cv)
        slope = math.nan if av <= 0 else math.log(av) * _safe_function_value(ftype, x0v, av, bv, cv)
    else:  # Logarithme
        discriminant = math.nan
        roots = [1.0] if av > 0 and av != 1 else []
        vertex_x, vertex_y = 1.0, 0.0
        try:
            denominator = x0v * math.log(av) if x0v > 0 and av > 0 and av != 1 else 0.0
            slope = 1.0 / denominator if denominator != 0 and math.isfinite(denominator) else math.nan
        except (ValueError, OverflowError, ZeroDivisionError):
            slope = math.nan
    fx0 = _safe_function_value(ftype, x0v, av, bv, cv)
    return dict(av=av, bv=bv, cv=cv, x0v=x0v, discriminant=discriminant, roots=roots,
                fx0=fx0, slope=slope, vertexX=vertex_x, vertexY=vertex_y, ftype=ftype)


def build_expression(ftype, a, b, c):
    A = a or '0'
    if ftype == 'Quadratic':
        return '%sx² %s %sx %s %s' % (A, sign(js_number(b)), js_str(abs(num(b))),
                                       sign(js_number(c)), js_str(abs(num(c))))
    if ftype == 'Affine':
        return '%sx %s %s' % (A, sign(js_number(b)), js_str(abs(num(b))))
    if ftype == 'Power':
        return 'x^%s' % A
    if ftype == 'Exponential':
        return '%sˣ' % (a or 'e')
    return 'log₍%s₎(x)' % (a or '10')


def analysis_rows(tab, v, expression, rng):
    """Construit les lignes de résultats adaptées à la fonction sélectionnée."""
    fn = format_number
    kind = v.get('ftype', 'Quadratic')
    domain = {
        'Quadratic': ('ℝ', 'Continue sur ℝ'),
        'Affine': ('ℝ', 'Continue sur ℝ'),
        'Power': ('ℝ (selon l’exposant)', 'Le domaine dépend de l’exposant'),
        'Exponential': ('ℝ (si a > 0)', 'Continue sur ℝ si a > 0'),
        'Logarithm': (']0, +∞[', 'Continue sur ]0, +∞[ si a > 0 et a ≠ 1'),
    }.get(kind, ('—', '—'))
    limits = {
        'Quadratic': [('lim x → +∞', '+∞ si a > 0, −∞ si a < 0'), ('lim x → −∞', '+∞ si a > 0, −∞ si a < 0'), ('Asymptotes', 'Aucune')],
        'Affine': [('lim x → +∞', '+∞ si a > 0, −∞ si a < 0'), ('lim x → −∞', '−∞ si a > 0, +∞ si a < 0'), ('Asymptotes', 'Aucune')],
        'Power': [('lim x → +∞', 'Dépend de l’exposant'), ('lim x → −∞', 'Dépend de l’exposant'), ('Asymptotes', 'Dépend de l’exposant')],
        'Exponential': [('lim x → +∞', '+∞ si a > 1 ; 0 si 0 < a < 1'), ('lim x → −∞', '0 si a > 1 ; +∞ si 0 < a < 1'), ('Asymptotes', 'y = 0 si a > 0 et a ≠ 1')],
        'Logarithm': [('lim x → 0⁺', '—∞ si a > 1 ; +∞ si 0 < a < 1'), ('lim x → +∞', '+∞ si a > 1 ; −∞ si 0 < a < 1'), ('Asymptotes', 'x = 0')],
    }.get(kind, [])
    root_rows = [('Racines réelles', ', '.join(fn(r) for r in v['roots']) if v['roots'] else 'Aucune racine réelle')]
    if kind == 'Affine' and v['av'] == 0 and v['bv'] == 0:
        root_rows = [('Racines réelles', 'Tous les réels (fonction nulle)')]
    if kind == 'Quadratic' and v['av'] == 0 and v['bv'] == 0 and v['cv'] == 0:
        root_rows = [('Racines réelles', 'Tous les réels (fonction nulle)')]
    if kind == 'Quadratic' and not (v['av'] == 0 and v['bv'] == 0 and v['cv'] == 0):
        root_rows = [('Discriminant Δ', fn(v['discriminant']))] + [
            ('x₁', fn(v['roots'][0]) if len(v['roots']) > 0 else 'Aucune racine réelle'),
            ('x₂', fn(v['roots'][1]) if len(v['roots']) > 1 else 'Aucune deuxième racine')]
    if kind == 'Quadratic':
        variation = [('Sommet', 'x = %s' % fn(v['vertexX'])),
                     ('Variation', 'dépend du signe de a (%s)' % ('minimum' if v['av'] > 0 else 'maximum' if v['av'] < 0 else 'fonction affine'))]
    elif kind == 'Affine':
        variation = [('Pente', fn(v['av'])), ('Variation', 'croissante' if v['av'] > 0 else 'décroissante' if v['av'] < 0 else 'constante')]
    else:
        variation = [('Point de référence', '(%s, %s)' % (fn(v['vertexX']), fn(v['vertexY']))),
                     ('Variation', 'voir le domaine et les paramètres de la fonction')]
    rows = {
        'Domain': [('D(f)', domain[0]), ('Continuité', domain[1]), ('Type', kind)],
        'Limits': limits,
        'Variations': variation,
        'Roots': root_rows,
        'Points': [('P₀', '(%s, %s)' % (fn(v['x0v']), fn(v['fx0']))),
                   ('Point de référence', '(%s, %s)' % (fn(v['vertexX']), fn(v['vertexY']))),
                   ('Fenêtre', rng)],
        'Tangent': [('Point', '(%s, %s)' % (fn(v['x0v']), fn(v['fx0']))),
                    ('Pente f′(x₀)', fn(v['slope'])),
                    ('Équation', 'y = %s(x − %s) + %s' % (fn(v['slope']), fn(v['x0v']), fn(v['fx0'])))],
        'Graph': [('Moteur', 'Tracé Canvas'), ('Échantillonnage', 'aperçu graphique'), ('Expression', expression)],
    }
    return rows.get(tab, [('Information', 'Aucune donnée disponible')])


# ════════════════════════════════════════════════════════════════════════════
#  Outils d'interface : échelle, polices, texte
# ty section no ameliorena , anamboarna ny interface d'utilisateur .
#

SCALE = 1.0
_fonts = {}
FAMILIES = {}


def px(n):
    return max(1, int(round(n * SCALE))) if n else 0


def _pick(cands, available, default):
    for c in cands:
        if c.lower() in available:
            return available[c.lower()]
    return default


def init_fonts(root):
    avail = {f.lower(): f for f in tkfont.families(root)}
    FAMILIES['sans'] = _pick(['Geist', 'Inter', 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', 'Roboto',
                              'Noto Sans', 'DejaVu Sans', 'Arial', 'Helvetica'], avail, 'TkDefaultFont')
    FAMILIES['light'] = _pick(['Segoe UI Light', 'Inter Light', 'Helvetica Neue Light', 'Roboto Light'],
                              avail, FAMILIES['sans'])
    FAMILIES['mono'] = _pick(['Geist Mono', 'JetBrains Mono', 'Cascadia Mono', 'SF Mono', 'Menlo',
                              'Consolas', 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New'],
                             avail, 'TkFixedFont')


def F(size, mono=False, bold=False, light=False):
    key = (size, mono, bold, light, SCALE)
    if key not in _fonts:
        fam = FAMILIES['mono'] if mono else (FAMILIES['light'] if light and not bold else FAMILIES['sans'])
        _fonts[key] = tkfont.Font(family=fam, size=-px(size), weight='bold' if bold else 'normal')
    return _fonts[key]


def trk(text, em):
    """Simule le letter-spacing (tracking) avec des espaces fines."""
    if not em:
        return text
    sp = '\u2009' if em >= .15 else '\u200a'
    return sp.join(text)


def mk_label(parent, text, size, color, bg, *, mono=False, bold=False, light=False, track=0,
             lh=None, wrap=0, anchor='w', justify='left'):
    f = F(size, mono, bold, light)
    line_px = px(lh if lh else size * 1.5)
    pad = max(0, (line_px - f.metrics('linespace')) // 2)
    return tk.Label(parent, text=trk(text, track), font=f, fg=color, bg=bg, bd=0, padx=0, pady=pad,
                    anchor=anchor, justify=justify, wraplength=px(wrap) if wrap else 0,
                    highlightthickness=0)


def line_color(bg, a=.10):
    return wa(a, bg)


def sep(parent, bg, h=1):
    return tk.Frame(parent, height=px(h) if h > 1 else 1, bg=bg, bd=0, highlightthickness=0)


class Box(tk.Frame):
    """Cadre bordé (1 px) avec padding interne : `.inner` reçoit le contenu."""

    def __init__(self, parent, bg, border, pad=0):
        super().__init__(parent, bg=bg, highlightthickness=1, highlightbackground=border,
                         highlightcolor=border, bd=0)
        self.inner = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self.inner.pack(fill='both', expand=True, padx=px(pad), pady=px(pad))


def bind_tree(widget, sequence, func):
    widget.bind(sequence, func, add='+')
    for child in widget.winfo_children():
        bind_tree(child, sequence, func)


# ════════════════════════════════════════════════════════════════════════════
#  Icônes (dessinées à la main, équivalents des icônes lucide-react)
# ════════════════════════════════════════════════════════════════════════════


class Icon(tk.Canvas):
    def __init__(self, parent, name, size, color, bg):
        self.size = px(size)
        super().__init__(parent, width=self.size, height=self.size, bg=bg, bd=0, highlightthickness=0)
        self.name, self.color = name, color
        self.draw()

    def set(self, color=None, bg=None, name=None):
        if color:
            self.color = color
        if bg:
            self.configure(bg=bg)
        if name:
            self.name = name
        self.draw()

    def draw(self):
        self.delete('all')
        k, col = self.size / 24.0, self.color
        w = max(1.0, 2 * k)

        def L(pts, smooth=False):
            self.create_line(*[v * k for p in pts for v in p], fill=col, width=w,
                             capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=smooth)

        def O(cx, cy, r, fill=''):
            self.create_oval((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k,
                             outline=col, width=w, fill=fill)

        def PG(pts):
            self.create_polygon(*[v * k for p in pts for v in p], outline=col, fill='', width=w,
                                joinstyle=tk.ROUND)

        def RR(x1, y1, x2, y2, r):
            pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
                   x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
            self.create_polygon(*[v * k for v in pts], outline=col, fill='', width=w, smooth=True)

        n = self.name
        if n == 'function-square':
            RR(3, 3, 21, 21, 2)
            L([(9, 17), (10.8, 16.6), (11.8, 14.2), (11.8, 10), (12.1, 8.2), (15, 7)], True)
            L([(9, 11.2), (14.7, 11.2)])
        elif n == 'circle-help':
            O(12, 12, 10)
            L([(9.1, 9), (10, 7.4), (12, 7), (14, 7.5), (14.9, 10), (14, 11.8), (12, 13)], True)
            O(12, 17, .6, fill=col)
        elif n == 'check':
            L([(20, 6), (9, 17), (4, 12)])
        elif n == 'activity':
            L([(22, 12), (18, 12), (15, 21), (9, 3), (6, 12), (2, 12)])
        elif n == 'rotate-ccw':
            self.create_arc(3 * k, 3 * k, 21 * k, 21 * k, start=180, extent=317, style=tk.ARC,
                            outline=col, width=w)
            L([(5.26, 5.74), (3, 8)])
            L([(3, 3), (3, 8), (8, 8)])
        elif n == 'chevron-down':
            L([(6, 9), (12, 15), (18, 9)])
        elif n == 'compass':
            O(12, 12, 10)
            PG([(16.24, 7.76), (14.12, 14.12), (7.76, 16.24), (9.88, 9.88)])
        elif n == 'waves':
            for dy in (0, 6, 12):
                L([(2, 6 + dy), (4.5, 7 + dy), (7, 6.2 + dy), (9.5, 5 + dy), (12, 5.1 + dy),
                   (14.5, 7 + dy), (17, 6.2 + dy), (19.5, 5 + dy), (22, 6 + dy)], True)
        elif n == 'sparkles':
            PG([(12, 2.4), (13.6, 8.6), (13.9, 10.1), (15.4, 10.4), (21.6, 12), (15.4, 13.6),
                (13.9, 13.9), (13.6, 15.4), (12, 21.6), (10.4, 15.4), (10.1, 13.9), (8.6, 13.6),
                (2.4, 12), (8.6, 10.4), (10.1, 10.1), (10.4, 8.6)])
            L([(20, 3), (20, 7)])
            L([(22, 5), (18, 5)])
            L([(4, 17), (4, 19)])
            L([(5, 18), (3, 18)])
        elif n == 'line-chart':
            L([(3, 3), (3, 21), (21, 21)])
            L([(19, 9), (14, 14), (10, 10), (7, 13)])
        elif n == 'bar-chart':
            L([(3, 3), (3, 21), (21, 21)])
            L([(18, 17), (18, 9)])
            L([(13, 17), (13, 5)])
            L([(8, 17), (8, 14)])
        elif n == 'arrow-up-right':
            L([(7, 7), (17, 7), (17, 17)])
            L([(7, 17), (17, 7)])


# ════════════════════════════════════════════════════════════════════════════
#  Widgets interactifs
# Ireo champ ireo no mi encpsule ny boutons, ireo element graphiques rehetra .
# ty code ity ihan kou no mamokatr sy afahan mitantan ireo ny teste local ity apk ity

# ════════════════════════════════════════════════════════════════════════════


class FlatButton(tk.Frame):
    """Bouton plat avec survol : [icône] + texte, bordure optionnelle."""

    def __init__(self, master, text, *, fg, bg, hfg=None, hbg=None, border=None, hborder=None,
                 size=10, track=.18, bold=False, icon=None, icon_size=15, padx=16, pady=12,
                 gap=8, command=None, expand=False, mono=False):
        self.cfg = dict(fg=fg, bg=bg, hfg=hfg or fg, hbg=hbg or bg, border=border, hborder=hborder or border)
        self.hover = False
        self.command = command
        super().__init__(master, bg=bg, bd=0, highlightthickness=1 if border else 0,
                         highlightbackground=border or bg, highlightcolor=border or bg, cursor='hand2')
        self.inner = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self.inner.pack(padx=px(padx), pady=px(pady), expand=True)
        self.icon = None
        if icon:
            self.icon = Icon(self.inner, icon, icon_size, fg, bg)
            self.icon.pack(side='left', padx=(0, px(gap)))
        self.label = mk_label(self.inner, text, size, fg, bg, bold=bold, track=track, mono=mono)
        self.label.pack(side='left')
        for wdg in (self, self.inner, self.label) + ((self.icon,) if self.icon else ()):
            wdg.bind('<Enter>', lambda e: self._set_hover(True))
            wdg.bind('<Leave>', lambda e: self._set_hover(False))
            wdg.bind('<Button-1>', self._click)
        self.apply()

    def _set_hover(self, state):
        self.hover = state
        self.apply()

    def _click(self, _e):
        if self.command:
            self.command()

    def style(self, **kw):
        self.cfg.update(kw)
        self.apply()

    def set_bold(self, bold):
        self.label.configure(font=F(10, bold=bold))

    def set_icon(self, name):
        if self.icon:
            self.icon.set(name=name)

    def apply(self):
        c = self.cfg
        fg = c['hfg'] if self.hover else c['fg']
        bg = c['hbg'] if self.hover else c['bg']
        bd = c['hborder'] if self.hover else c['border']
        for wdg in (self, self.inner):
            wdg.configure(bg=bg)
        if c['border']:
            self.configure(highlightbackground=bd, highlightcolor=bd)
        self.label.configure(fg=fg, bg=bg)
        if self.icon:
            self.icon.set(color=fg, bg=bg)


class Select(tk.Frame):
    """Équivalent du <select> stylé : bordure verte au focus, liste déroulante sombre."""

    def __init__(self, master, values, value, command):
        self.border = wa(.15, SELECT_BG)
        super().__init__(master, bg=SELECT_BG, bd=0, highlightthickness=1, highlightbackground=self.border,
                         highlightcolor=LIME, takefocus=True, cursor='hand2')
        self.values, self.value, self.command, self.pop = values, value, command, None
        self.label = mk_label(self, value, 14, FG, SELECT_BG, lh=20)
        self.label.pack(fill='x', padx=px(12), pady=px(12))
        self.chev = Icon(self, 'chevron-down', 16, wa(.5, SELECT_BG), SELECT_BG)
        self.chev.place(relx=1.0, x=-px(12) - px(16), y=px(14))
        for wdg in (self, self.label, self.chev):
            wdg.bind('<Button-1>', self._click)
        self.bind('<Down>', lambda e: self._step(1))
        self.bind('<Up>', lambda e: self._step(-1))
        self.bind('<Return>', lambda e: self._open())
        self.bind('<space>', lambda e: self._open())

    def owns(self, widget):
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, 'master', None)
        return False

    def set(self, value):
        self.value = value
        self.label.configure(text=value)

    def _choose(self, value):
        self._close()
        self.set(value)
        self.command(value)

    def _step(self, d):
        i = (self.values.index(self.value) + d) % len(self.values)
        self._choose(self.values[i])

    def _click(self, _e):
        self.focus_set()
        self._close() if self.pop else self._open()

    def _open(self):
        if self.pop:
            return
        self.update_idletasks()
        w, rowh = self.winfo_width(), px(36)
        pop = tk.Toplevel(self)
        pop.overrideredirect(True)
        pop.configure(bg=self.border)
        pop.geometry('%dx%d+%d+%d' % (w, rowh * len(self.values) + 2, self.winfo_rootx(),
                                      self.winfo_rooty() + self.winfo_height() - 1))
        body = tk.Frame(pop, bg=SELECT_BG, bd=0)
        body.pack(fill='both', expand=True, padx=1, pady=1)
        for v in self.values:
            cur = v == self.value
            row = tk.Frame(body, bg=SELECT_BG, height=rowh, cursor='hand2')
            row.pack(fill='x')
            row.pack_propagate(False)
            lab = mk_label(row, v, 14, LIME if cur else FG, SELECT_BG, lh=20)
            lab.pack(side='left', padx=px(12), fill='y')

            def enter(_e, r=row, l=lab):
                r.configure(bg=wa(.10, SELECT_BG)); l.configure(bg=wa(.10, SELECT_BG))

            def leave(_e, r=row, l=lab):
                r.configure(bg=SELECT_BG); l.configure(bg=SELECT_BG)

            for wdg in (row, lab):
                wdg.bind('<Enter>', enter)
                wdg.bind('<Leave>', leave)
                wdg.bind('<ButtonRelease-1>', lambda e, val=v: self._choose(val))
        pop.bind('<Escape>', lambda e: self._close())
        pop.bind('<Button-1>', self._outside)
        self.pop = pop
        pop.after(20, self._grab)

    def _grab(self):
        if self.pop:
            try:
                self.pop.grab_set()
                self.pop.focus_force()
            except tk.TclError:
                pass

    def _outside(self, e):
        p = self.pop
        if p and not (p.winfo_rootx() <= e.x_root < p.winfo_rootx() + p.winfo_width() and
                      p.winfo_rooty() <= e.y_root < p.winfo_rooty() + p.winfo_height()):
            self._close()

    def _close(self):
        if self.pop:
            try:
                self.pop.grab_release()
            except tk.TclError:
                pass
            self.pop.destroy()
            self.pop = None
            self.focus_set()


class MiniGraph(tk.Canvas):
    """Trace une fonction réelle sur une grille, en ignorant les points hors domaine."""
    def __init__(self, parent, ftype='Quadratic', a=1.0, b=-4.0, c=3.0, window='-10, 10'):
        super().__init__(parent, height=px(208), bg=GRAPH_BG, bd=0, highlightthickness=1,
                         highlightbackground=line_color(GRAPH_BG))
        self.ftype, self.a, self.b, self.c = ftype, a, b, c
        self.xmin, self.xmax = self._parse_window(window)
        self.bind('<Configure>', lambda e: self.redraw())

    @staticmethod
    def _parse_window(value):
        """Lit la fenêtre x sous la forme « min, max » et utilise [-10, 10] si elle est invalide."""
        try:
            parts = [float(part.strip().replace('−', '-')) for part in value.split(',')]
            if len(parts) == 2 and all(math.isfinite(x) for x in parts) and parts[0] < parts[1]:
                return parts[0], parts[1]
        except (ValueError, AttributeError):
            pass
        return -10.0, 10.0

    def redraw(self):
        self.delete('all')
        w, h = max(self.winfo_width(), 10), max(self.winfo_height(), 10)
        step, gc = px(40), blend('#ffffff', GRAPH_BG, .035)
        for x in range(0, w, step):
            self.create_line(x, 0, x, h, fill=gc)
        for y in range(0, h, step):
            self.create_line(0, y, w, y, fill=gc)
        margin = px(14)
        plot_w, plot_h = max(1, w - 2 * margin), max(1, h - 2 * margin)
        samples = []
        # Un échantillonnage uniforme suffit à l'aperçu ; les valeurs extrêmes sont écrêtées.
        for i in range(401):
            x = self.xmin + (self.xmax - self.xmin) * i / 400
            y = _safe_function_value(self.ftype, x, self.a, self.b, self.c)
            samples.append((x, y))
        finite_y = [y for _, y in samples if math.isfinite(y)]
        if not finite_y:
            self.create_text(w / 2, h / 2, text='Aucune valeur réelle dans cette fenêtre',
                             fill=wa(.55, GRAPH_BG), font=F(10))
            return
        ymin, ymax = min(finite_y), max(finite_y)
        if math.isclose(ymin, ymax):
            ymin, ymax = ymin - 1, ymax + 1
        # Les courbes trop raides sont limitées à une fenêtre verticale lisible.
        center, span = (ymin + ymax) / 2, max(ymax - ymin, 1e-9)
        ymin, ymax = center - span * .60, center + span * .60
        def project(x, y):
            return (margin + (x - self.xmin) / (self.xmax - self.xmin) * plot_w,
                    h - margin - (y - ymin) / (ymax - ymin) * plot_h)
        # Axes x=0 et y=0 ne sont dessinés que s'ils traversent la fenêtre.
        axis = wa(.28, GRAPH_BG)
        if self.xmin <= 0 <= self.xmax:
            xx, _ = project(0, ymin)
            self.create_line(xx, margin, xx, h - margin, fill=axis, dash=(3, 4))
        if ymin <= 0 <= ymax:
            _, yy = project(self.xmin, 0)
            self.create_line(margin, yy, w - margin, yy, fill=axis, dash=(3, 4))
        segment = []
        for x, y in samples:
            if math.isfinite(y) and ymin - 2 * span <= y <= ymax + 2 * span:
                segment.extend(project(x, max(ymin, min(ymax, y))))
            else:
                if len(segment) >= 4:
                    self.create_line(*segment, fill=LIME, width=px(2), smooth=False)
                segment = []
        if len(segment) >= 4:
            self.create_line(*segment, fill=LIME, width=px(2), smooth=False)
        self.create_text(px(10), h - px(7), anchor='sw',
                         text='x ∈ [%s, %s]' % (format_number(self.xmin), format_number(self.xmax)),
                         font=F(9), fill=wa(.45, GRAPH_BG))
        self.create_text(w - px(10), px(8), anchor='ne', text='LIVE PLOT',
                         font=F(9), fill=LIME)


# ════════════════════════════════════════════════════════════════════════════
#  Application
# App amokarana ny parametre  , ny calcul , ary ireo onglet tkinter .
# Les StringVar  izay mampifanarak ny champ de saisie ami'ny affichage ny resultat 
# main()  mijanona ho points afhana milance ny program .
# ════════════════════════════════════════════════════════════════════════════


class App:
    DEFAULTS = dict(functionType='Quadratic', a='1', b='-4', c='3', x0='2', rng='−10, 10')

    def __init__(self, root):
        global SCALE
        self.root = root
        if sys.platform.startswith('win'):
            SCALE = max(1.0, root.winfo_fpixels('1i') / 96.0)
        init_fonts(root)
        root.title('nexus Calc — Scientific Function Workspace')
        root.configure(bg=BG)
        root.geometry('%dx%d' % (px(1280), px(900)))
        root.minsize(px(360), px(480))
        self._set_window_icon()

        # état (équivalent des useState)
        self.function_type = self.DEFAULTS['functionType']
        self.active_tab = 'Overview'
        self.active_page = 'WORKSPACE'
        self.notes_text = ''
        # La saisie et le résultat sont conservés même lorsque l'utilisateur change d'onglet.
        self.scientific_expression = tk.StringVar(value='sin(pi / 2) + sqrt(16)')
        self.scientific_result = tk.StringVar(value='Prêt à calculer')
        self.computed = True
        self.vars = {k: tk.StringVar(value=self.DEFAULTS[k]) for k in ('a', 'b', 'c', 'x0', 'rng')}
        for var in self.vars.values():
            var.trace_add('write', lambda *_: self.on_change())

        self.W = 0
        self.main_mode = None
        self.out_w = 0
        self._layout_job = None
        self._last_size = (0, 0)

        self._style_scrollbar()
        wrap = tk.Frame(root, bg=BG)
        wrap.pack(fill='both', expand=True)
        self.vsb = ttk.Scrollbar(wrap, orient='vertical', style='Nexus.Vertical.TScrollbar')
        self.vsb.pack(side='right', fill='y')
        self.cv = tk.Canvas(wrap, bg=BG, bd=0, highlightthickness=0, yscrollincrement=px(40),
                            yscrollcommand=self.vsb.set)
        self.cv.pack(side='left', fill='both', expand=True)
        self.vsb.configure(command=self.cv.yview)

        self.build_header()
        self.build_main()
        self.build_footer()

        self.cv.bind('<Configure>', self.on_configure)
        root.bind_all('<MouseWheel>', self.on_wheel)
        root.bind_all('<Button-4>', lambda e: self.on_wheel(e, 1))
        root.bind_all('<Button-5>', lambda e: self.on_wheel(e, -1))
        root.bind_all('<Button-1>', self.on_global_click, add='+')
        self.refresh_all()

    # ── divers ─────────────────────────────────────────────────────────────
    def _set_window_icon(self):
        try:
            img = tk.PhotoImage(width=32, height=32)
            img.put(LIME, to=(0, 0, 32, 32))
            img.put(BG, to=(8, 8, 24, 10))
            img.put(BG, to=(8, 8, 10, 24))
            img.put(BG, to=(8, 15, 20, 17))
            img.put(BG, to=(14, 8, 24, 10))
            self.root.iconphoto(True, img)
            self._icon = img
        except tk.TclError:
            pass

    def _style_scrollbar(self):
        st = ttk.Style(self.root)
        try:
            st.theme_use('clam')
        except tk.TclError:
            pass
        st.configure('Nexus.Vertical.TScrollbar', background=wa(.18, BG), troughcolor=BG, bordercolor=BG,
                     darkcolor=BG, lightcolor=BG, arrowcolor=BG, gripcount=0, relief='flat')
        st.map('Nexus.Vertical.TScrollbar', background=[('active', wa(.32, BG)), ('pressed', LIME)])
        st.layout('Nexus.Vertical.TScrollbar', [('Vertical.Scrollbar.trough', {
            'sticky': 'ns', 'children': [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})]})])

    def bp(self, n):
        return self.W >= px(n)

    def on_wheel(self, e, direction=None):
        if self.select.pop:
            return
        if direction is None:
            d = e.delta
            n = -int(d / 120) if abs(d) >= 120 else (-1 if d > 0 else 1)
        else:
            n = -direction
        if e.state & 1 and self.over_tabs(e.widget):  # Maj + molette : défiler les onglets
            self.tabs_cv.xview_scroll(n, 'units')
        elif not (e.state & 1):
            self.cv.yview_scroll(n, 'units')

    def over_tabs(self, widget):
        while widget is not None:
            if widget is self.tabs_cv:
                return True
            widget = getattr(widget, 'master', None)
        return False

    def on_global_click(self, e):
        w = e.widget
        if isinstance(w, tk.Entry) or (isinstance(w, tk.Widget) and self.select.owns(w)):
            return
        if isinstance(w, tk.Widget) and not str(w).startswith(str(self.select) + '.'):
            try:
                if w.winfo_toplevel() is self.root:
                    self.cv.focus_set()
            except tk.TclError:
                pass

    # ── en-tête ────────────────────────────────────────────────────────────
    def build_header(self):
        self.hdr = tk.Frame(self.cv, bg=HEADER_BG, bd=0)
        self.hdr_win = self.cv.create_window(0, 0, anchor='nw', window=self.hdr)
        self.hdr_inner = tk.Frame(self.hdr, bg=HEADER_BG, bd=0)
        tk.Frame(self.hdr, bg=line_color(HEADER_BG), height=1).place(x=0, rely=1.0, y=-1, relwidth=1)

        # logo
        self.logo = tk.Frame(self.hdr_inner, bg=HEADER_BG)
        box = tk.Frame(self.logo, bg=LIME, width=px(36), height=px(36), highlightthickness=1,
                       highlightbackground=wa(.30, HEADER_BG), bd=0)
        box.pack(side='left')
        box.pack_propagate(False)
        Icon(box, 'function-square', 21, BG, LIME).place(relx=.5, rely=.5, anchor='center')
        title = tk.Frame(self.logo, bg=HEADER_BG)
        title.pack(side='left', padx=(px(12), 0))
        mk_label(title, 'OK', 15, FG, HEADER_BG, bold=True, track=.16, lh=22).pack(side='left')
        mk_label(title, '//', 15, LIME, HEADER_BG, bold=True, track=.16, lh=22).pack(side='left')
        mk_label(title, 'CALC', 15, FG, HEADER_BG, bold=True, track=.16, lh=22).pack(side='left')

        # Navigation réellement connectée aux pages internes de l'application.
        self.nav = tk.Frame(self.hdr_inner, bg=HEADER_BG)
        self.nav_btns = {}
        for i, item in enumerate(NAV_ITEMS):
            tk.Frame(self.nav, bg=line_color(HEADER_BG), width=1).pack(side='left', fill='y')
            btn = FlatButton(self.nav, item, fg=LIME if i == 0 else wa(.60, HEADER_BG), bg=HEADER_BG,
                             hbg=wa(.10, HEADER_BG), size=10, track=.18, padx=20, pady=8,
                             command=lambda page=item: self.set_page(page))
            btn.pack(side='left')
            self.nav_btns[item] = btn

        # Le bouton GUIDE ouvre une page d'aide dédiée.
        self.guide = FlatButton(self.hdr_inner, 'GUIDE', fg=wa(.60, HEADER_BG), hfg=FG, bg=HEADER_BG,
                                icon='circle-help', icon_size=16, size=10, track=.16, padx=0, pady=0,
                                command=lambda: self.set_page('GUIDE'))

    def layout_header(self, x0, pad, inner_w, W, y):
        self.cv.coords(self.hdr_win, 0, y)
        self.cv.itemconfigure(self.hdr_win, width=W, height=px(74) + 1)
        self.hdr_inner.place(x=x0 + pad, y=0, width=inner_w, height=px(74))
        self.hdr_inner.update_idletasks()
        items = [self.logo] + ([self.nav] if self.bp(768) else []) + [self.guide]
        if not self.bp(768):
            self.nav.place_forget()
        widths = [i.winfo_reqwidth() for i in items]
        gap = (inner_w - sum(widths)) / max(1, len(items) - 1)
        x = 0.0
        for it, wd in zip(items, widths):
            it.place(x=int(x), y=(px(74) - it.winfo_reqheight()) // 2)
            x += wd + gap

    # ── pied de page ───────────────────────────────────────────────────────
    def build_footer(self):
        self.ftr = tk.Frame(self.cv, bg=BG, bd=0)
        self.ftr_win = self.cv.create_window(0, 0, anchor='nw', window=self.ftr)
        tk.Frame(self.ftr, bg=line_color(BG), height=1).place(x=0, y=0, relwidth=1)
        self.ftr_inner = tk.Frame(self.ftr, bg=BG)
        self.ftr_left = mk_label(self.ftr_inner, 'NEXUS//CALC · PRECISION WITHOUT FRICTION', 10,
                                 wa(.35, BG), BG, track=.16)
        self.ftr_right = tk.Frame(self.ftr_inner, bg=BG)
        mk_label(self.ftr_right, 'BUILD 01.24.26', 10, wa(.35, BG), BG, track=.16).pack(side='left')
        mk_label(self.ftr_right, '●', 10, LIME, BG, track=.16).pack(side='left', padx=(px(12), 0))

    def layout_footer(self, x0, pad, inner_w, W, y):
        self.cv.coords(self.ftr_win, 0, y)
        self.cv.itemconfigure(self.ftr_win, width=W, height=px(57))
        self.ftr_inner.place(x=x0 + pad, y=px(21), width=inner_w, height=px(15))
        self.ftr_left.place(x=0, y=0)
        if self.bp(640):
            self.ftr_right.place(relx=1.0, anchor='ne', y=0)
        else:
            self.ftr_right.place_forget()

    # ── hero (dessiné sur le canvas pour garder la grille visible) ────────
    def draw_hero(self, left, y, inner_w):
        cv, md = self.cv, self.bp(768)
        cv.delete('hero')
        y += px(64) if md else px(48)
        # eyebrow
        cv.create_line(left, y + px(8), left + px(40), y + px(8), fill=LIME, tags='hero')
        cv.create_text(left + px(52), y + px(8), anchor='w', text=trk('SCIENTIFIC COMPUTING / 01', .25),
                       font=F(10), fill=LIME, tags='hero')
        y += px(15) + px(24)
        # h1
        size = 96 if md else 48
        maxw = min(px(768), inner_w)
        while size > 28 and F(size, light=True).measure('Understand every') > maxw:
            size -= 2
        f = F(size, light=True)
        lh = int(px(size) * .98)
        for text, col in (('Understand every', FG), ('dimension of a function.', wa(.45, BG))):
            for ln in self.wrap(text, f, maxw):
                cv.create_text(left, y + (lh - f.metrics('linespace')) // 2, anchor='nw', text=ln, font=f,
                               fill=col, tags='hero')
                y += lh
        # paragraphe
        y += px(28)
        f = F(14)
        for ln in self.wrap('A precise workspace for symbolic analysis, visual intuition and numerical '
                            'exploration — built for the way scientists think.', f, min(px(576), inner_w)):
            cv.create_text(left, y + (px(24) - f.metrics('linespace')) // 2, anchor='nw', text=ln, font=f,
                           fill=wa(.55, BG), tags='hero')
            y += px(24)
        # pastilles
        y += px(40)
        f, cx, cy, gap = F(10), left, y, px(12)
        for chip in ('SYMBOLIC ENGINE', 'REAL-TIME GRAPHING', 'SI UNITS READY'):
            t = trk(chip, .16)
            w, h = f.measure(t) + px(24) + 2, px(15) + px(16) + 2
            if cx + w > left + inner_w and cx > left:
                cx, cy = left, cy + h + gap
            cv.create_rectangle(cx, cy, cx + w - 1, cy + h - 1, outline=wa(.15, BG), tags='hero')
            cv.create_text(cx + w / 2, cy + h / 2, text=t, font=f, fill=wa(.45, BG), tags='hero')
            cx += w + gap
        return cy + px(15) + px(16) + 2 + px(40)

    @staticmethod
    def wrap(text, font, maxw):
        lines, cur = [], ''
        for word in text.split(' '):
            t = (cur + ' ' + word) if cur else word
            if font.measure(t) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
        return lines

    # ── zone principale ────────────────────────────────────────────────────
    def build_main(self):
        self.main = tk.Frame(self.cv, bg=BG, bd=0)
        self.main_win = self.cv.create_window(0, 0, anchor='nw', window=self.main)
        self.build_aside()
        self.build_output()

    def build_aside(self):
        self.aside = Box(self.main, ASIDE_BG, line_color(ASIDE_BG), 20)
        a = self.aside.inner
        top = tk.Frame(a, bg=ASIDE_BG)
        top.pack(fill='x', pady=(0, px(28)))
        mk_label(top, 'INPUT PARAMETERS', 10, wa(.45, ASIDE_BG), ASIDE_BG, track=.22).pack(side='left')
        mk_label(top, 'LIVE', 10, LIME, ASIDE_BG).pack(side='right')

        mk_label(a, 'FUNCTION TYPE', 10, wa(.45, ASIDE_BG), ASIDE_BG, track=.16).pack(fill='x', pady=(0, px(8)))
        self.select = Select(a, FUNCTIONS, self.function_type, self.on_function_change)
        self.select.pack(fill='x', pady=(0, px(28)))

        exp = tk.Frame(a, bg=ASIDE_BG)
        exp.pack(fill='x', pady=(0, px(28)))
        tk.Frame(exp, bg=LIME, width=px(2)).pack(side='left', fill='y')
        ei = tk.Frame(exp, bg=ASIDE_BG)
        ei.pack(side='left', fill='x', expand=True, padx=(px(16), 0))
        mk_label(ei, 'f(x) =', 10, wa(.45, ASIDE_BG), ASIDE_BG, track=.18).pack(fill='x', pady=(0, px(8)))
        self.exp_label = mk_label(ei, '', 20, FG, ASIDE_BG, light=True, lh=28, wrap=220)
        self.exp_label.pack(fill='x')

        rows = tk.Frame(a, bg=ASIDE_BG)
        rows.pack(fill='x')
        self.entries = {}
        spec = [('a', 'a', True), ('b', 'b', True), ('c', 'c', True), ('x0', 'x₀', True), ('rng', 'WINDOW', False)]
        for i, (key, text, mono_lbl) in enumerate(spec):
            row = tk.Frame(rows, bg=ASIDE_BG)
            row.pack(fill='x', pady=(0 if i == 0 else px(16), 0))
            line = tk.Frame(row, bg=ASIDE_BG)
            line.pack(fill='x', pady=(0, px(12)))
            if mono_lbl:
                mk_label(line, text, 14, LIME, ASIDE_BG, mono=True, lh=20).pack(side='left')
            else:
                mk_label(line, text, 14, wa(.55, ASIDE_BG), ASIDE_BG, lh=20).pack(side='left')
            holder = tk.Frame(line, bg=ASIDE_BG, width=px(96), height=px(20))
            holder.pack(side='right')
            holder.pack_propagate(False)
            ent = tk.Entry(holder, textvariable=self.vars[key], justify='right', font=F(14, mono=True),
                           bg=ASIDE_BG, fg=FG, insertbackground=FG, bd=0, relief='flat',
                           highlightthickness=0, selectbackground=LIME, selectforeground=BG,
                           disabledbackground=ASIDE_BG)
            ent.pack(fill='both', expand=True)
            self.entries[key] = ent
            tk.Frame(row, bg=line_color(ASIDE_BG), height=1).pack(fill='x')

        self.calc_btn = FlatButton(a, 'CALCULATE / UPDATE', fg=BG, bg=LIME, hbg='#ffffff', bold=True,
                                   icon='check', icon_size=15, size=10, track=.18, padx=16, pady=12,
                                   command=self.handle_calculate)
        self.calc_btn.pack(fill='x', pady=(px(28), 0))
        self.reset_btn = FlatButton(a, 'RESET WORKSPACE', fg=wa(.65, ASIDE_BG), hfg=FG, bg=ASIDE_BG,
                                    border=wa(.15, ASIDE_BG), hborder=wa(.40, ASIDE_BG), icon='rotate-ccw',
                                    icon_size=14, size=10, track=.18, padx=16, pady=12, command=self.reset)
        self.reset_btn.pack(fill='x', pady=(px(12), 0))

    def build_output(self):
        self.output = tk.Frame(self.main, bg=OUT_BG, highlightthickness=1,
                               highlightbackground=line_color(OUT_BG), bd=0)
        head = tk.Frame(self.output, bg=OUT_BG)
        head.pack(fill='x')
        hi = tk.Frame(head, bg=OUT_BG)
        hi.pack(fill='x', padx=px(20), pady=px(16))
        left = tk.Frame(hi, bg=OUT_BG)
        left.pack(side='left')
        mk_label(left, 'ANALYSIS / OUTPUT', 10, LIME, OUT_BG, track=.20).pack(anchor='w')
        self.subtitle = mk_label(left, '', 14, wa(.50, OUT_BG), OUT_BG, lh=20)
        self.subtitle.pack(anchor='w', pady=(px(4), 0))
        self.synced = tk.Frame(hi, bg=OUT_BG)
        tk.Frame(self.synced, bg=LIME, width=px(8), height=px(8)).pack(side='left', padx=(0, px(8)))
        mk_label(self.synced, 'SYNCED', 10, wa(.40, OUT_BG), OUT_BG, track=.14).pack(side='left')
        self.synced.pack(side='right')
        tk.Frame(self.output, bg=line_color(OUT_BG), height=1).pack(fill='x')

        # onglets (défilement horizontal Maj + molette si trop étroit)
        self.tabs_cv = tk.Canvas(self.output, height=px(47), bg=OUT_BG, bd=0, highlightthickness=0)
        self.tabs_cv.pack(fill='x')
        self.tabs_inner = tk.Frame(self.tabs_cv, bg=OUT_BG)
        self.tabs_cv.create_window(px(8), px(8), anchor='nw', window=self.tabs_inner)
        self.tab_btns = {}
        for t in TABS:
            b = FlatButton(self.tabs_inner, t, fg=wa(.45, OUT_BG), hfg=FG, bg=OUT_BG, hbg=wa(.10, OUT_BG),
                           size=10, track=.12, padx=12, pady=8, command=lambda t=t: self.set_tab(t))
            b.pack(side='left', padx=(0, px(4)))
            self.tab_btns[t] = b
        self.tabs_inner.bind('<Configure>', lambda e: self.tabs_cv.configure(
            scrollregion=(0, 0, self.tabs_inner.winfo_reqwidth() + px(16), px(47))))
        tk.Frame(self.output, bg=line_color(OUT_BG), height=1).pack(fill='x')

        self.body_pad = tk.Frame(self.output, bg=OUT_BG)
        self.body_pad.pack(fill='both', expand=True)
        self.body = tk.Frame(self.body_pad, bg=OUT_BG)
        self.body.pack(fill='both', expand=True, padx=px(28), pady=px(28))

    # ── état / événements ─────────────────────────────────────────────────
    def on_function_change(self, value):
        self.function_type = value
        self.refresh_all()

    def on_change(self):
        if hasattr(self, 'body'):
            self.refresh_all()

    def set_tab(self, tab):
        self._save_notes()
        self.active_page = 'WORKSPACE'
        self.active_tab = tab
        self.refresh_all()

    def set_page(self, page):
        """Navigue entre Workspace, Méthodes, Notes, À propos et Guide."""
        self._save_notes()
        self.active_page = page
        if page == 'WORKSPACE':
            self.active_tab = 'Overview'
        self.refresh_all()

    def handle_calculate(self):
        self.computed = False
        self.calc_btn.set_icon('activity')
        self.root.after(140, self._calc_done)

    def _calc_done(self):
        self.computed = True
        self.calc_btn.set_icon('check')

    def reset(self):
        d = self.DEFAULTS
        self.function_type = d['functionType']
        self.select.set(self.function_type)
        for key in ('a', 'b', 'c', 'x0', 'rng'):
            self.vars[key].set(d[key])
        self.active_tab = 'Overview'
        self.active_page = 'WORKSPACE'
        self.refresh_all()

    def state(self):
        return dict(a=self.vars['a'].get(), b=self.vars['b'].get(), c=self.vars['c'].get(),
                    x0=self.vars['x0'].get(), rng=self.vars['rng'].get())

    def refresh_all(self):
        s = self.state()
        self.expression = build_expression(self.function_type, s['a'], s['b'], s['c'])
        self.values = compute_values(s['a'], s['b'], s['c'], s['x0'], self.function_type)
        self.exp_label.configure(text=self.expression)
        self.subtitle.configure(text='Symbolic resolution · %s' % self.function_type)
        for t, b in self.tab_btns.items():
            if self.active_page == 'WORKSPACE' and t == self.active_tab:
                b.style(fg=BG, bg=LIME, hfg=BG, hbg=LIME)
                b.set_bold(True)
            else:
                b.style(fg=wa(.45, OUT_BG), bg=OUT_BG, hfg=FG, hbg=wa(.10, OUT_BG))
                b.set_bold(False)
        for page, b in self.nav_btns.items():
            if page == self.active_page:
                b.style(fg=LIME, bg=HEADER_BG, hfg=FG, hbg=HEADER_BG)
            else:
                b.style(fg=wa(.60, HEADER_BG), bg=HEADER_BG, hfg=FG, hbg=wa(.10, HEADER_BG))
        self.render_body()
        self.update_heights()

    # ── rendu des onglets ─────────────────────────────────────────────────
    def render_body(self):
        for w in self.body.winfo_children():
            w.destroy()
        for i in range(4):
            self.body.grid_columnconfigure(i, weight=0, uniform='', minsize=0)
        bw = max(px(120), self.out_w - 2 - 2 * px(28)) if self.out_w else px(600)
        if not self.bp(768):
            bw = max(px(120), self.out_w - 2 - 2 * px(20)) if self.out_w else px(300)
        self.body.pack_configure(padx=px(28) if self.bp(768) else px(20),
                                 pady=px(28) if self.bp(768) else px(20))
        if self.active_page != 'WORKSPACE':
            self.build_info_page(self.body, bw, self.active_page)
        elif self.active_tab == 'Overview':
            self.build_overview(self.body, bw)
        elif self.active_tab == 'Scientific Calculator':
            self.build_scientific_calculator(self.body, bw)
        else:
            self.build_analysis(self.body, bw)

    def build_info_page(self, parent, bw, page):
        """Construit les pages Méthodes, Notes, À propos et Guide."""
        pad = px(24) if self.bp(768) else px(16)
        card = Box(parent, OUT_BG, line_color(OUT_BG), pad)
        inner = card.inner
        titles = {
            'METHODS': ('METHODS / MÉTHODES', 'Comment les résultats sont calculés'),
            'NOTES': ('NOTES / NOTES PERSONNELLES', 'Conservez vos observations pour cette session'),
            'ABOUT': ('ABOUT / À PROPOS', 'NEXUS//CALC — Scientific Function Workspace'),
            'GUIDE': ('GUIDE / AIDE RAPIDE', 'Comment utiliser le calculateur'),
        }
        eyebrow, heading = titles.get(page, titles['ABOUT'])
        mk_label(inner, eyebrow, 10, LIME, OUT_BG, track=.20).pack(anchor='w')
        mk_label(inner, heading, 22, FG, OUT_BG, light=True, lh=30,
                 wrap=max(px(200), bw - 2 * pad)).pack(anchor='w', pady=(px(10), px(18)))

        if page == 'METHODS':
            sections = [
                ('1. Fonction quadratique', 'f(x) = ax² + bx + c. Discriminant : Δ = b² − 4ac. Si Δ > 0, x₁ = (−b − √Δ)/(2a) et x₂ = (−b + √Δ)/(2a). Si Δ = 0, x₀ = −b/(2a) est la racine double. Sommet : S(−b/(2a), f(−b/(2a))). Dérivée : f′(x) = 2ax + b.'),
                ('2. Fonction affine', 'f(x) = ax + b. Coefficient directeur : a. Ordonnée à l’origine : b. Si a ≠ 0, la racine est x = −b/a. Dérivée : f′(x) = a. La fonction est croissante si a > 0, décroissante si a < 0 et constante si a = 0.'),
                ('3. Fonction puissance', 'Dans ce programme : f(x) = xᵃ, où a est l’exposant. Pour les valeurs où la dérivée existe, f′(x) = a·xᵃ⁻¹. Pour a > 0, f(0) = 0. Le domaine réel dépend de l’exposant (notamment pour les exposants non entiers).'),
                ('4. Fonction exponentielle', 'Dans ce programme : f(x) = aˣ, où a est la base. Pour a > 0, f′(x) = aˣ ln(a). Si a > 1, la fonction est croissante ; si 0 < a < 1, elle est décroissante ; si a = 1, elle est constante égale à 1.'),
                ('5. Fonction logarithme', 'f(x) = logₐ(x) = ln(x)/ln(a), avec x > 0, a > 0 et a ≠ 1. Dérivée : f′(x) = 1/(x ln(a)). La racine est x = 1. La droite x = 0 est une asymptote verticale.'),
                ('6. Tangente et limites', 'Tangente au point d’abscisse x₀ : y = f′(x₀)(x − x₀) + f(x₀), si la fonction et sa dérivée y sont définies. Une limite décrit le comportement de f(x) lorsque x approche une valeur ou ±∞.'),
                ('7. Calcul numérique', 'Les fonctions trigonométriques attendent des angles en radians. Constantes disponibles : pi, e et tau. Fonctions disponibles notamment : sin, cos, tan, asin, acos, atan, sqrt, log, ln, log2, exp, abs, floor, ceil et factorial.')
            ]
            for title, body in sections:
                mk_label(inner, title, 14, LIME, OUT_BG, bold=True, lh=22).pack(anchor='w', pady=(px(10), px(4)))
                mk_label(inner, body, 12, wa(.78, OUT_BG), OUT_BG, lh=20,
                         wrap=max(px(200), bw - 2 * pad)).pack(anchor='w', pady=(0, px(8)))
        elif page == 'NOTES':
            mk_label(inner, 'Écrivez vos formules, démonstrations, exemples et questions. Utilisez ENREGISTRER pour conserver les notes pendant cette session.',
                     12, wa(.60, OUT_BG), OUT_BG, lh=19).pack(anchor='w', pady=(0, px(12)))
            self.notes_widget = tk.Text(inner, height=14, wrap='word', undo=True, font=F(12),
                                        bg=PREVIEW_BG, fg=FG, insertbackground=FG,
                                        selectbackground=LIME, selectforeground=BG,
                                        relief='flat', bd=0, padx=px(12), pady=px(12))
            self.notes_widget.pack(fill='both', expand=True)
            self.notes_widget.insert('1.0', self.notes_text)
            self.notes_widget.bind('<FocusOut>', lambda _e: self._save_notes())
            self.notes_widget.bind('<KeyRelease>', lambda _e: self._save_notes())
            actions = tk.Frame(inner, bg=OUT_BG)
            actions.pack(fill='x', pady=(px(12), 0))
            FlatButton(actions, 'ENREGISTRER LES NOTES', fg=BG, bg=LIME, hbg='#ffffff',
                       size=10, padx=14, pady=9, command=self._save_notes).pack(side='left')
            FlatButton(actions, 'EFFACER', fg=wa(.65, OUT_BG), hfg=FG, bg=OUT_BG, hbg=wa(.10, OUT_BG),
                       border=wa(.15, OUT_BG), size=10, padx=14, pady=9,
                       command=self._clear_notes).pack(side='left', padx=(px(8), 0))
        elif page == 'ABOUT':
            for label, value in [
                ('APPLICATION', 'NEXUS//CALC — Scientific Function Workspace'),
                ('OBJECTIF', 'Étudier des fonctions, calculer leurs propriétés et visualiser leurs courbes.'),
                ('FONCTIONS', 'Quadratique · Affine · Puissance · Exponentielle · Logarithme'),
                ('INTERFACE', 'Python et Tkinter pour les fenêtres, champs, boutons et onglets.'),
                ('GRAPHIQUES', 'Matplotlib disponible : %s' % ('oui' if MATPLOTLIB_AVAILABLE else 'non — Canvas de secours actif')),
                ('CALCULS', 'Module math pour les opérations numériques et évaluation sécurisée des expressions.'),
                ('DÉPENDANCE', 'Installer Matplotlib avec : python -m pip install matplotlib numpy'),
            ]:
                mk_label(inner, label, 10, LIME, OUT_BG, track=.16).pack(anchor='w', pady=(px(8), px(3)))
                mk_label(inner, value, 13, FG, OUT_BG, lh=20,
                         wrap=max(px(200), bw - 2 * pad)).pack(anchor='w')
            FlatButton(inner, 'REVENIR AU WORKSPACE', fg=BG, bg=LIME, hbg='#ffffff',
                       size=10, padx=16, pady=10, command=lambda: self.set_page('WORKSPACE')).pack(
                           anchor='w', pady=(px(22), 0))
        else:
            steps = [
                ('01 — Choisir une fonction', 'Dans INPUT PARAMETERS, choisissez Quadratic, Affine, Power, Exponential ou Logarithm. Les paramètres a, b et c changent de sens selon le type ; reportez-vous à METHODS.'),
                ('02 — Régler les paramètres', 'Saisissez les coefficients, l’abscisse x₀ et la fenêtre horizontale du graphique sous la forme −10, 10. Utilisez le point comme séparateur décimal.'),
                ('03 — Lire les résultats', 'Overview donne un résumé. Domain précise le domaine, Limits les limites, Variations les variations, Roots les racines, Points les coordonnées et Tangent l’équation de la tangente.'),
                ('04 — Explorer la courbe', 'Ouvrez Graph pour afficher la courbe Matplotlib. Les outils de navigation permettent le zoom, le déplacement et la réinitialisation de la vue. La courbe se met à jour lorsque vous changez les paramètres.'),
                ('05 — Calculatrice scientifique', 'Essayez sin(pi/2), sqrt(81), log(100), ln(e) ou 2^8. Les angles trigonométriques sont en radians. Utilisez les parenthèses pour clarifier les opérations.'),
                ('06 — Notes et navigation', 'NOTES permet de garder vos remarques durant la session. METHODS contient les formules, ABOUT présente les technologies et le bouton GUIDE revient à ces instructions.'),
            ]
            for title, body in steps:
                mk_label(inner, title, 14, LIME, OUT_BG, bold=True, lh=22).pack(anchor='w', pady=(px(10), px(4)))
                mk_label(inner, body, 12, wa(.78, OUT_BG), OUT_BG, lh=20,
                         wrap=max(px(200), bw - 2 * pad)).pack(anchor='w', pady=(0, px(8)))
            FlatButton(inner, 'OUVRIR LES MÉTHODES', fg=BG, bg=LIME, hbg='#ffffff',
                       size=10, padx=16, pady=10, command=lambda: self.set_page('METHODS')).pack(
                           anchor='w', pady=(px(8), 0))

    def _save_notes(self):
        if hasattr(self, 'notes_widget') and self.notes_widget.winfo_exists():
            self.notes_text = self.notes_widget.get('1.0', 'end-1c')

    def _clear_notes(self):
        self.notes_text = ''
        if hasattr(self, 'notes_widget') and self.notes_widget.winfo_exists():
            self.notes_widget.delete('1.0', 'end')

    def metric(self, parent, label, value, detail, icon, inner_w):
        box = Box(parent, OUT_BG, line_color(OUT_BG), 20)
        i = box.inner
        top = tk.Frame(i, bg=OUT_BG)
        top.pack(fill='x', pady=(0, px(32)))
        mk_label(top, label, 10, wa(.40, OUT_BG), OUT_BG, track=.20).pack(side='left')
        Icon(top, icon, 24, LIME, OUT_BG).pack(side='right')
        mk_label(i, value, 24, FG, OUT_BG, mono=True, lh=32, wrap=inner_w).pack(fill='x')
        mk_label(i, detail, 12, wa(.40, OUT_BG), OUT_BG, lh=16, wrap=inner_w).pack(fill='x', pady=(px(8), 0))
        return box

    def stat(self, parent, name, value, cell_w):
        fr = tk.Frame(parent, bg=PREVIEW_BG)
        n = mk_label(fr, name, 10, wa(.45, PREVIEW_BG), PREVIEW_BG, track=.12)
        v = mk_label(fr, value, 10, FG, PREVIEW_BG, bold=True, track=.12, wrap=cell_w / SCALE)
        need = F(10).measure(trk(name + ' ', .12)) + F(10, bold=True).measure(trk(value, .12))
        if need <= cell_w:
            n.pack(side='left')
            v.pack(side='left', padx=(px(4), 0))
        else:
            n.pack(anchor='w')
            v.pack(anchor='w')
        return fr

    def _derivative_summary(self, v):
        """Formule synthétique de dérivée selon la fonction sélectionnée."""
        if self.function_type == 'Quadratic':
            return '%sx %s %s' % (format_number(2 * v['av']), sign(v['bv']), js_str(abs(v['bv'])))
        if self.function_type == 'Affine':
            return format_number(v['av'])
        if self.function_type == 'Power':
            return '%s·x^(%s)' % (format_number(v['av']), format_number(v['av'] - 1))
        if self.function_type == 'Exponential':
            return 'f(x)·ln(a)' if v['av'] > 0 else 'non définie'
        return '1 / (x·ln(a))'

    def build_overview(self, parent, bw):
        v = self.values
        lg, sm, gap = self.bp(1024), self.bp(640), px(20)
        if lg:
            lw = (bw - gap) * 10 // 22
            rw = bw - gap - lw
        else:
            lw = rw = bw
        # colonne gauche : métriques
        left = tk.Frame(parent, bg=OUT_BG)
        cols = 2 if (not lg and sm) else 1
        mw = (lw - gap * (cols - 1)) // cols
        inner = mw - 2 - 2 * px(20)
        deriv = self._derivative_summary(v)
        roots = ', '.join(format_number(r) for r in v['roots']) if v['roots'] else '∅'
        domain = ('x > 0' if self.function_type == 'Logarithm' else
                  'Dépend de l’exposant' if self.function_type == 'Power' else 'ℝ')
        discr = ('Δ = %s' % format_number(v['discriminant']) if self.function_type == 'Quadratic'
                 else 'Solutions de f(x)=0')
        data = [('DOMAIN', domain, 'Domain of definition', 'compass'),
                ('DERIVATIVE', deriv, 'First order differential', 'waves'),
                ('ROOTS', roots, discr, 'sparkles')]
        for c in range(cols):
            left.grid_columnconfigure(c, weight=1, uniform='m')
        for idx, (lab, val, det, ic) in enumerate(data):
            r, c = divmod(idx, cols)
            self.metric(left, lab, val, det, ic, inner).grid(
                row=r, column=c, sticky='nsew', padx=(0, gap if c < cols - 1 else 0),
                pady=(0, gap if r < (len(data) - 1) // cols else 0))
        # colonne droite : aperçu
        right = Box(parent, PREVIEW_BG, line_color(PREVIEW_BG), 28 if self.bp(768) else 20)
        ri = right.inner
        top = tk.Frame(ri, bg=PREVIEW_BG)
        top.pack(fill='x')
        Icon(top, 'line-chart', 24, wa(.35, PREVIEW_BG), PREVIEW_BG).pack(side='right', anchor='n')
        tl = tk.Frame(top, bg=PREVIEW_BG)
        tl.pack(side='left', fill='x', expand=True)
        mk_label(tl, 'FUNCTION PREVIEW', 10, wa(.40, PREVIEW_BG), PREVIEW_BG, track=.20).pack(anchor='w')
        pad = 28 if self.bp(768) else 20
        mk_label(tl, 'f(x) = %s' % self.expression, 24, LIME, PREVIEW_BG, mono=True, lh=32,
                 wrap=(rw - 2 - 2 * px(pad) - px(24) - px(12)) / SCALE).pack(anchor='w', pady=(px(12), 0))
        MiniGraph(ri, self.function_type, v['av'], v['bv'], v['cv'], self.vars['rng'].get()).pack(
            fill='x', pady=(px(32), 0))
        tk.Frame(ri, bg=line_color(PREVIEW_BG), height=1).pack(fill='x', pady=(px(20), px(16)))
        stats = tk.Frame(ri, bg=PREVIEW_BG)
        stats.pack(fill='x')
        cell = (rw - 2 - 2 * px(pad) - 2 * px(12)) // 3
        for c in range(3):
            stats.grid_columnconfigure(c, weight=1, uniform='s')
        for c, (n, val) in enumerate([
                ('REF:', '(%s, %s)' % (format_number(v['vertexX']), format_number(v['vertexY']))),
                ('f(%s):' % format_number(v['x0v']), format_number(v['fx0'])),
                ('SLOPE:', format_number(v['slope']))]):
            self.stat(stats, n, val, cell).grid(row=0, column=c, sticky='nw', padx=(0, px(12) if c < 2 else 0))
        # placement
        if lg:
            parent.grid_columnconfigure(0, weight=10, uniform='o')
            parent.grid_columnconfigure(1, weight=0, minsize=gap)
            parent.grid_columnconfigure(2, weight=12, uniform='o')
            left.grid(row=0, column=0, sticky='nsew')
            right.grid(row=0, column=2, sticky='nsew')
        else:
            parent.grid_columnconfigure(0, weight=1)
            left.grid(row=0, column=0, sticky='nsew')
            right.grid(row=1, column=0, sticky='nsew', pady=(gap, 0))

    # ── onglet calculatrice scientifique ───────────────────────────────────
    # Eto amin'ito champ ito ilay amokarana ilay calculatrice scientifique, 
    # rah azavaina tsotsotr de azo lazaina tsy tena parfait be mou zan , ka nefa mavita calcul simple ihan iza 
    # ireto ny fonctionnalite  tena misongadin ao :
    # x , / , - , + , * , ^ , sin , cos , tan , ln , log , sqrt , exp , pi , e , !
    #  
    def scientific_insert(self, value):
        """Ajoute un symbole ou une fonction à l'expression courante."""
        current = self.scientific_expression.get()
        if value == 'AC':
            self.scientific_expression.set('')
            self.scientific_result.set('Saisie effacée')
        elif value == 'DEL':
            self.scientific_expression.set(current[:-1])
        elif value == '=':
            self.calculate_scientific()
        else:
            self.scientific_expression.set(current + value)

    def calculate_scientific(self):
        """Évalue l'expression courante et présente un message utile en cas d'erreur."""
        try:
            self.scientific_result.set(scientific_eval(self.scientific_expression.get()))
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError) as exc:
            self.scientific_result.set('Erreur : ' + str(exc))

    def build_scientific_calculator(self, parent, bw):
        """Dessine l'interface de calcul scientifique dans le style sombre du workspace."""
        gap = px(16)
        pad = px(22) if self.bp(768) else px(14)
        card = Box(parent, OUT_BG, line_color(OUT_BG), 0)
        card.grid(row=0, column=0, sticky='nsew')
        parent.grid_columnconfigure(0, weight=1)
        inside = card.inner
        heading = tk.Frame(inside, bg=OUT_BG)
        heading.pack(fill='x', padx=pad, pady=(pad, px(8)))
        mk_label(heading, 'SCIENTIFIC ENGINE / 02', 10, LIME, OUT_BG, track=.20).pack(anchor='w')
        mk_label(inside, 'Calculate beyond the basics.', 27, FG, OUT_BG, light=True,
                 wrap=max(px(220), bw - 2 * pad)).pack(anchor='w', padx=pad, pady=(0, px(6)))
        mk_label(inside, 'Trigonométrie · logarithmes · puissances · constantes · racines', 12,
                 wa(.50, OUT_BG), OUT_BG, wrap=max(px(220), bw - 2 * pad)).pack(anchor='w', padx=pad, pady=(0, gap))

        # Écran d'entrée et zone de résultat : police monospace pour lire les formules.
        screen = tk.Frame(inside, bg=PREVIEW_BG, highlightthickness=1,
                          highlightbackground=line_color(PREVIEW_BG))
        screen.pack(fill='x', padx=pad, pady=(0, gap))
        mk_label(screen, 'EXPRESSION', 9, wa(.45, PREVIEW_BG), PREVIEW_BG, track=.18).pack(
            anchor='w', padx=px(14), pady=(px(12), px(4)))
        entry = tk.Entry(screen, textvariable=self.scientific_expression, font=F(19, mono=True),
                         bg=PREVIEW_BG, fg=FG, insertbackground=LIME, bd=0, relief='flat',
                         highlightthickness=0)
        entry.pack(fill='x', padx=px(14), pady=(0, px(12)))
        entry.bind('<Return>', lambda _event: self.calculate_scientific())
        tk.Frame(screen, bg=line_color(PREVIEW_BG), height=1).pack(fill='x')
        result_line = tk.Frame(screen, bg=PREVIEW_BG)
        result_line.pack(fill='x', padx=px(14), pady=px(12))
        mk_label(result_line, 'RESULT', 9, LIME, PREVIEW_BG, track=.18).pack(side='left')
        mk_label(result_line, '', 17, FG, PREVIEW_BG, mono=True).pack(side='left', padx=(px(12), 0))
        result_label = result_line.winfo_children()[-1]
        result_label.configure(textvariable=self.scientific_result, wraplength=max(px(180), bw - 2 * pad - px(90)))

        # Pavé de touches en grille ; chaque bouton appelle la même fonction d'insertion.
        keys = [
            [('sin(', 'function'), ('cos(', 'function'), ('tan(', 'function'), ('ln(', 'function'), ('log(', 'function')],
            [('asin(', 'function'), ('acos(', 'function'), ('atan(', 'function'), ('sqrt(', 'function'), ('exp(', 'function')],
            [('π', 'function'), ('e', 'function'), ('^', 'function'), ('(', 'normal'), (')', 'normal')],
            [('7', 'normal'), ('8', 'normal'), ('9', 'normal'), ('÷', 'normal'), ('DEL', 'utility')],
            [('4', 'normal'), ('5', 'normal'), ('6', 'normal'), ('×', 'normal'), ('AC', 'utility')],
            [('1', 'normal'), ('2', 'normal'), ('3', 'normal'), ('−', 'normal'), ('%', 'normal')],
            [('0', 'normal'), ('.', 'normal'), ('+', 'normal'), ('!', 'normal'), ('=', 'primary')],
        ]
        keypad = tk.Frame(inside, bg=OUT_BG)
        keypad.pack(fill='x', padx=pad, pady=(0, pad))
        for col in range(5):
            keypad.grid_columnconfigure(col, weight=1, uniform='scientific-keys')
        for row_index, row in enumerate(keys):
            for col_index, (label, kind) in enumerate(row):
                # Le style différencie fonctions, commandes secondaires et validation.
                bg = LIME if kind == 'primary' else (PREVIEW_BG if kind == 'function' else SELECT_BG)
                fg = BG if kind == 'primary' else (LIME if kind == 'function' else FG)
                button = tk.Button(keypad, text=label, command=lambda v=label: self._scientific_key(v),
                                   font=F(12, mono=kind == 'normal', bold=kind == 'primary'),
                                   bg=bg, fg=fg, activebackground=LIME, activeforeground=BG,
                                   bd=0, relief='flat', cursor='hand2', padx=4, pady=10)
                button.grid(row=row_index, column=col_index, sticky='nsew', padx=px(3), pady=px(3))
        mk_label(inside, 'Exemples : sin(pi/2) · sqrt(81) · log(100) · 2^8', 10,
                 wa(.40, OUT_BG), OUT_BG, mono=True, wrap=max(px(220), bw - 2 * pad)).pack(
                     anchor='w', padx=pad, pady=(0, pad))

    def _scientific_key(self, value):
        """Traduit les touches spéciales en opérations de saisie ou de calcul."""
        if value == '=':
            self.calculate_scientific()
        elif value == '!':
            # Ty makasik io touche factoriel io, izan oe mamadika ireo isa ho lasa symbol  
            # izay jou de afaka ievitena ny anoratan  factorial( aoriany ny isa na ny parenthèse,
            # ary rah tsy evitena izan dia met iteraka invalida expression « 5factorial( ».
            current = self.scientific_expression.get().rstrip()
            match = re.search(r'(\d+(?:\.\d+)?|\([^()]*\))$', current)
            if match:
                operand = match.group(1)
                self.scientific_expression.set(current[:match.start()] + 'factorial(' + operand + ')')
            else:
                self.scientific_expression.set(current + 'factorial(')
        elif value == '%':
            self.scientific_expression.set(self.scientific_expression.get() + '/100')
        else:
            self.scientific_insert(value)

    def build_matplotlib_graph(self, parent, bw):
        """Affiche la fonction courante avec Matplotlib et une barre de navigation."""
        if not MATPLOTLIB_AVAILABLE:
            mk_label(parent, 'Matplotlib n’est pas installé. Exécutez : python -m pip install matplotlib numpy',
                     13, LIME, OUT_BG, wrap=bw).pack(anchor='w')
            MiniGraph(parent, self.function_type, self.values['av'], self.values['bv'],
                      self.values['cv'], self.vars['rng'].get()).pack(fill='x', pady=(px(12), 0))
            return
        card = Box(parent, OUT_BG, line_color(OUT_BG), px(12))
        card.grid(row=0, column=0, sticky='nsew')
        parent.grid_columnconfigure(0, weight=1)
        inner = card.inner
        mk_label(inner, 'COURBE DE LA FONCTION', 10, LIME, OUT_BG, track=.20).pack(anchor='w')
        mk_label(inner, 'f(x) = ' + self.expression, 18, FG, OUT_BG, mono=True,
                 wrap=max(px(220), bw - px(30))).pack(anchor='w', pady=(px(8), px(12)))
        try:
            parts = [float(part.strip().replace('−', '-')) for part in self.vars['rng'].get().split(',')]
            if (len(parts) != 2 or not all(math.isfinite(z) for z in parts)
                    or parts[0] >= parts[1] or abs(parts[0]) > 1_000_000
                    or abs(parts[1]) > 1_000_000 or parts[1] - parts[0] > 1_000_000):
                raise ValueError
            xmin, xmax = parts
        except (ValueError, TypeError):
            xmin, xmax = -10.0, 10.0
        xs = np.linspace(xmin, xmax, 1000)
        ys = [_safe_function_value(self.function_type, float(x), self.values['av'],
                                   self.values['bv'], self.values['cv']) for x in xs]
        ys = np.asarray(ys, dtype=float)
        ys[~np.isfinite(ys)] = np.nan
        finite = ys[np.isfinite(ys)]
        fig = Figure(figsize=(8.0, 4.8), dpi=100, facecolor=OUT_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(GRAPH_BG)
        ax.plot(xs, ys, color='#b8ff35', linewidth=2.2, label='f(x)')
        ax.axhline(0, color='#8191a2', linewidth=.8, alpha=.7)
        ax.axvline(0, color='#8191a2', linewidth=.8, alpha=.7)
        ax.grid(True, color='#536273', alpha=.28, linestyle='--')
        ax.set_xlim(xmin, xmax)
        if finite.size:
            low, high = np.nanpercentile(finite, [2, 98])
            if math.isclose(float(low), float(high)):
                low, high = float(low) - 1, float(high) + 1
            margin = max((float(high) - float(low)) * .15, .5)
            ax.set_ylim(float(low) - margin, float(high) + margin)
        ax.set_xlabel('x', color=FG)
        ax.set_ylabel('f(x)', color=FG)
        ax.set_title('Représentation graphique', color=FG, loc='left')
        ax.tick_params(colors='#c4ccd5')
        for spine in ax.spines.values():
            spine.set_color('#354555')
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=inner)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(canvas, inner, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(fill='x')
        if not finite.size:
            mk_label(inner, 'Aucune valeur réelle dans la fenêtre choisie.', 11, LIME, OUT_BG).pack(anchor='w')

    def build_analysis(self, parent, bw):
        if self.active_tab == 'Graph':
            return self.build_matplotlib_graph(parent, bw)
        lg, gap = self.bp(1024), px(20)
        cw = (bw - gap) // 2 if lg else bw
        pad = 28 if self.bp(768) else 20
        # carte de gauche
        card = Box(parent, OUT_BG, line_color(OUT_BG), pad)
        ci = card.inner
        head = tk.Frame(ci, bg=OUT_BG)
        head.pack(fill='x', pady=(0, px(24)))
        Icon(head, 'bar-chart', 24, LIME, OUT_BG).pack(side='left', padx=(0, px(12)))
        hl = tk.Frame(head, bg=OUT_BG)
        hl.pack(side='left')
        mk_label(hl, self.active_tab.upper(), 10, LIME, OUT_BG, track=.20).pack(anchor='w')
        mk_label(hl, 'Exact symbolic evaluation', 14, wa(.45, OUT_BG), OUT_BG, lh=20).pack(
            anchor='w', pady=(px(4), 0))
        row_w = cw - 2 - 2 * px(pad)
        for label, value in analysis_rows(self.active_tab, self.values, self.expression, self.vars['rng'].get()):
            row = tk.Frame(ci, bg=OUT_BG)
            row.pack(fill='x')
            line = tk.Frame(row, bg=OUT_BG)
            line.pack(fill='x', pady=px(16))
            mk_label(line, label, 14, wa(.45, OUT_BG), OUT_BG, lh=20).pack(side='left', anchor='n')
            mk_label(line, value, 14, FG, OUT_BG, mono=True, lh=20, wrap=row_w * .62 / SCALE,
                     anchor='e', justify='right').pack(side='right', anchor='n')
            tk.Frame(row, bg=line_color(OUT_BG), height=1).pack(fill='x')
        # carte de droite (note scientifique)
        note = tk.Frame(parent, bg=NOTE_BG, highlightthickness=1, highlightbackground=NOTE_BORDER, bd=0)
        ni = tk.Frame(note, bg=NOTE_BG)
        ni.pack(fill='both', expand=True, padx=px(pad), pady=px(pad))
        tk.Frame(ni, bg=NOTE_BG, width=1, height=max(0, px(290) - 2 - 2 * px(pad))).pack(side='left')
        bottom = tk.Frame(ni, bg=NOTE_BG)
        bottom.pack(side='bottom', fill='x')
        tk.Frame(bottom, bg=blend(LIME, NOTE_BG, .20), height=1).pack(fill='x')
        brow = tk.Frame(bottom, bg=NOTE_BG)
        brow.pack(fill='x', pady=(px(16), 0))
        mk_label(brow, 'PRECISION: DOUBLE', 10, wa(.40, NOTE_BG), NOTE_BG, track=.12).pack(side='left')
        Icon(brow, 'arrow-up-right', 24, LIME, NOTE_BG).pack(side='right')
        topf = tk.Frame(ni, bg=NOTE_BG)
        topf.pack(side='top', fill='x')
        mk_label(topf, 'SCIENTIFIC NOTE', 10, LIME, NOTE_BG, track=.20).pack(anchor='w')
        mk_label(topf, 'Every result is kept close to its mathematical origin, so you can move from intuition '
                       'to proof without changing tools.', 20, wa(.80, NOTE_BG), NOTE_BG, light=True, lh=32,
                 wrap=min(448, (cw - 2 - 2 * px(pad)) / SCALE)).pack(anchor='w', pady=(px(20), 0))
        if lg:
            parent.grid_columnconfigure(0, weight=1, uniform='g')
            parent.grid_columnconfigure(1, weight=0, minsize=gap)
            parent.grid_columnconfigure(2, weight=1, uniform='g')
            card.grid(row=0, column=0, sticky='nsew')
            note.grid(row=0, column=2, sticky='nsew')
        else:
            parent.grid_columnconfigure(0, weight=1)
            card.grid(row=0, column=0, sticky='nsew')
            note.grid(row=1, column=0, sticky='nsew', pady=(gap, 0))

    # ── mise en page globale ──────────────────────────────────────────────
    def on_configure(self, e):
        size = (e.width, e.height)
        if size == self._last_size:
            return
        self._last_size = size
        if self._layout_job:
            self.root.after_cancel(self._layout_job)
        self._layout_job = self.root.after(15, self.layout)

    def layout(self):
        self._layout_job = None
        cv = self.cv
        W = max(cv.winfo_width(), px(320))
        self.W = W
        md = self.bp(768)
        pad = px(40) if md else px(20)
        cw = min(W, px(1440))
        x0 = (W - cw) // 2
        left, inner_w = x0 + pad, cw - 2 * pad
        self.geom = (x0, pad, inner_w)

        self.layout_header(x0, pad, inner_w, W, 0)
        self.hero_bottom = self.draw_hero(left, px(75), inner_w)

        # grille principale
        aside_w = px(300) if md else inner_w
        gap = px(16)
        self.out_w = inner_w - aside_w - gap if md else inner_w
        mode = 'md' if md else 'sm'
        self.main.grid_columnconfigure(0, weight=0, minsize=aside_w if md else 0)
        self.main.grid_columnconfigure(1, weight=1 if md else 0)
        if md:
            self.aside.grid(row=0, column=0, sticky='nsew', padx=(0, gap))
            self.output.grid(row=0, column=1, sticky='nsew', padx=0, pady=0)
            self.synced.pack(side='right') if self.bp(640) else None
        else:
            self.main.grid_columnconfigure(0, weight=1)
            self.aside.grid(row=0, column=0, sticky='nsew', padx=0)
            self.output.grid(row=1, column=0, sticky='nsew', pady=(gap, 0))
        if not self.bp(640):
            self.synced.pack_forget()
        else:
            self.synced.pack(side='right')
        self.exp_label.configure(wraplength=max(px(80), aside_w - 2 - 2 * px(20) - px(18)))
        cv.coords(self.main_win, left, self.hero_bottom)
        cv.itemconfigure(self.main_win, width=inner_w)
        self.main_mode = mode
        self.render_body()
        self.update_heights()

    def update_heights(self):
        if not self.W:
            return
        cv = self.cv
        self.root.update_idletasks()
        x0, pad, inner_w = self.geom
        mh = self.main.winfo_reqheight()
        cv.itemconfigure(self.main_win, height=mh)
        y = self.hero_bottom + mh + px(64)
        self.layout_footer(x0, pad, inner_w, self.W, y)
        total = y + px(57)
        total = max(total, cv.winfo_height())
        cv.configure(scrollregion=(0, 0, self.W, total))
        # grille de fond
        cv.delete('grid')
        gc = blend('#ffffff', BG, .035 * .30)
        step = px(48)
        for x in range(0, self.W, step):
            cv.create_line(x, 0, x, total, fill=gc, tags='grid')
        for yy in range(0, total, step):
            cv.create_line(0, yy, self.W, yy, fill=gc, tags='grid')
        cv.tag_lower('grid')


def main():
    if sys.platform.startswith('win'):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    App(root)
    root.mainloop()

#  ito ny partie important ndrindr @ ty code
#  ty satrie raha tss io de ts afaka compiler io code io 
if __name__ == '__main__':
    main()
