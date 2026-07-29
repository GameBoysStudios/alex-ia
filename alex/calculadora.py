# -*- coding: utf-8 -*-
"""
Motor de calculo seguro para Alex (2.0 y Pro).
Compatible con Python 3.8+ / 3.14 (sin ast.Num).
"""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any, Optional

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _factorial_safe(n: float) -> float:
    if not float(n).is_integer():
        raise ValueError("factorial solo para enteros")
    n = int(n)
    if n < 0:
        raise ValueError("factorial de negativo")
    if n > 500:
        raise ValueError("factorial demasiado grande (max 500)")
    return float(math.factorial(n))


_FUNCS = {
    "sqrt": math.sqrt,
    "raiz": math.sqrt,
    "abs": abs,
    "fabs": math.fabs,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "factorial": _factorial_safe,
    "fact": _factorial_safe,
    "degrees": math.degrees,
    "radians": math.radians,
    "deg": math.degrees,
    "rad": math.radians,
    "pow": pow,
    "min": min,
    "max": max,
    "hypot": math.hypot,
}

_CONSTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

_PATRON_CALC = re.compile(
    r"(?:"
    r"cu[aá]nto\s+(?:es|vale|da)|"
    r"calcula(?:r)?|"
    r"resuelve|"
    r"opera(?:ci[oó]n)?|"
    r"haz\s+(?:la\s+)?cuenta|"
    r"compute|calculate|what(?:'s|\s+is)|"
    r"solve"
    r")\b",
    re.I,
)

_PATRON_PORCENTAJE = re.compile(
    r"(?:el\s+)?(\d+(?:[.,]\d+)?)\s*%\s*(?:de|of)\s*(\d+(?:[.,]\d+)?)",
    re.I,
)
_PATRON_RAIZ = re.compile(
    r"(?:ra[ií]z(?:\s+cuadrada)?\s+(?:de\s+)?|sqrt\s*(?:de\s+)?)"
    r"(\d+(?:[.,]\d+)?)",
    re.I,
)
_PATRON_POTENCIA = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:elevado\s+a(?:\s+la)?|a\s+la)\s*"
    r"(\d+(?:[.,]\d+)?)",
    re.I,
)

# Expresion aritmetica con al menos un digito y un operador/funcion
_RE_EXPR_ARIT = re.compile(
    r"("
    r"(?:"
    r"(?:sqrt|sin|cos|tan|log|ln|log10|log2|exp|abs|floor|ceil|round|"
    r"factorial|fact|pow|min|max|hypot|asin|acos|atan|degrees|radians|deg|rad|raiz)"
    r"\s*\([^()]*(?:\([^()]*\)[^()]*)*\)"
    r"|"
    r"\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?"
    r"|"
    r"[()+−\-*/^%×÷.]"
    r"|\s+"
    r")+"
    r")",
)


def parece_calculo(texto: str) -> bool:
    t = (texto or "").strip()
    if not t:
        return False
    if _PATRON_PORCENTAJE.search(t) or _PATRON_RAIZ.search(t):
        return True
    if _PATRON_POTENCIA.search(t):
        return True
    # 2+2, (3*4)/2, etc. — digito + operador + digito
    if re.search(r"\d", t) and re.search(r"[+−\-*/^%×÷]", t):
        return True
    if re.search(r"\d\s*!", t):
        return True
    if re.search(
        r"\b(?:sqrt|sin|cos|tan|log|ln|log10|exp|factorial|fact|abs|floor|ceil)\s*\(",
        t,
        re.I,
    ):
        return True
    if _PATRON_CALC.search(t) and re.search(r"\d", t):
        return True
    if re.search(r"\d", t) and re.search(
        r"\b(m[aá]s|menos|por|entre|dividido|multiplicado)\b",
        t,
        re.I,
    ):
        return True
    # Solo constante pi / e / tau si el mensaje es casi solo eso
    if re.fullmatch(r"\s*(?:pi|tau|e|π)\s*", t, re.I):
        return True
    return False


def _normalizar_expresion(texto: str) -> str:
    t = (texto or "").strip()

    # 1) Casos naturales especiales (antes de tocar el texto)
    m = _PATRON_PORCENTAJE.search(t)
    if m:
        a = m.group(1).replace(",", ".")
        b = m.group(2).replace(",", ".")
        return f"({a}/100)*{b}"

    m = _PATRON_RAIZ.search(t)
    if m:
        return f"sqrt({m.group(1).replace(',', '.')})"

    m = _PATRON_POTENCIA.search(t)
    if m:
        return f"({m.group(1).replace(',', '.')})**({m.group(2).replace(',', '.')})"

    m = re.search(r"\bfactorial\s+(?:de\s+)?(\d+)\b", t, re.I)
    if m:
        return f"factorial({m.group(1)})"
    m = re.search(r"\b(\d+)\s*!", t)
    if m:
        # Si solo es factorial (sin mas operadores), resolverlo
        if not re.search(r"[+−\-*/]", t):
            return f"factorial({m.group(1)})"

    # 2) Quitar prefijos de intencion ("cuanto es", "calcula"...)
    t = _PATRON_CALC.sub(" ", t)
    t = re.sub(r"^(?:me\s+puedes|puedes|por\s+favor|please)\s+", "", t, flags=re.I)
    t = re.sub(r"[¿?¡!]+", " ", t)
    t = t.strip(" :.=\t\n")

    # 3) Palabras operador → simbolos
    reemplazos = [
        (r"\bm[aá]s\b", "+"),
        (r"\bmenos\b", "-"),
        (r"\bpor\b", "*"),
        (r"\bmultiplicado\s+por\b", "*"),
        (r"\bentre\b", "/"),
        (r"\bdividido\s+(?:por|entre)\b", "/"),
        (r"\bsobre\b", "/"),
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
        (r"\btimes\b", "*"),
        (r"\bdivided\s+by\b", "/"),
    ]
    for pat, rep in reemplazos:
        t = re.sub(pat, rep, t, flags=re.I)

    t = t.replace("×", "*").replace("÷", "/").replace("−", "-")
    t = t.replace("^", "**")
    t = re.sub(r"√\s*\(", "sqrt(", t)
    t = re.sub(r"√\s*(\d+(?:[.,]\d+)?)", r"sqrt(\1)", t)
    t = re.sub(r"(\d),(\d)", r"\1.\2", t)

    # 4) Extraer la mejor subcadena con digitos + operadores (NO aceptar solo 'e')
    candidatos = []
    for m in _RE_EXPR_ARIT.finditer(t):
        frag = m.group(1).strip()
        frag_ns = re.sub(r"\s+", "", frag)
        if not frag_ns:
            continue
        tiene_digito = bool(re.search(r"\d", frag_ns))
        tiene_op = bool(re.search(r"[+−\-*/%()]|\*\*", frag_ns))
        tiene_func = bool(
            re.search(
                r"(?:sqrt|sin|cos|tan|log|ln|exp|abs|factorial|fact|floor|ceil|pow)",
                frag_ns,
                re.I,
            )
        )
        if tiene_digito and (tiene_op or tiene_func):
            candidatos.append(frag_ns)
        elif tiene_func and "(" in frag_ns:
            candidatos.append(frag_ns)

    if candidatos:
        # Preferir el mas largo con digitos
        t = max(candidatos, key=len)
    else:
        # Solo constantes explicitas: "pi", "e", "tau"
        m = re.fullmatch(r"\s*(pi|tau|e|π)\s*", t, re.I)
        if m:
            nombre = m.group(1).lower()
            return "pi" if nombre in ("pi", "π") else nombre
        # Ultimo intento: quedarnos con digitos y ops basicos
        t = re.sub(r"[^0-9a-zA-Z_+\-*/.()%]", "", t)
        t = re.sub(r"\s+", "", t)

    # 5) Yuxtaposicion implicita: 2(3+1) → 2*(3+1)
    t = re.sub(r"(\d)\(", r"\1*(", t)
    t = re.sub(r"\)(\d)", r")*\1", t)
    t = re.sub(r"\)\(", r")*(", t)

    return t


class _SafeEval(ast.NodeVisitor):
    def visit(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return self.visit(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("constante no numerica")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _BINOPS:
                raise ValueError(f"operador no permitido: {op_type.__name__}")
            left = self.visit(node.left)
            right = self.visit(node.right)
            if op_type is ast.Pow and (abs(left) > 1e6 or right > 1000):
                raise ValueError("potencia demasiado grande")
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("division por cero")
            return float(_BINOPS[op_type](left, right))

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _UNARY:
                raise ValueError("operador unario no permitido")
            return float(_UNARY[op_type](self.visit(node.operand)))

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("llamada no permitida")
            nombre = node.func.id.lower()
            if nombre not in _FUNCS:
                raise ValueError(f"funcion no permitida: {nombre}")
            args = [self.visit(a) for a in node.args]
            if node.keywords:
                raise ValueError("kwargs no permitidos")
            if len(args) > 5:
                raise ValueError("demasiados argumentos")
            return float(_FUNCS[nombre](*args))

        if isinstance(node, ast.Name):
            nombre = node.id.lower()
            if nombre in _CONSTS:
                return float(_CONSTS[nombre])
            if nombre in _FUNCS:
                raise ValueError(f"'{nombre}' necesita parentesis, ej. {nombre}(9)")
            raise ValueError(f"nombre desconocido: {node.id}")

        raise ValueError(f"nodo no permitido: {type(node).__name__}")


def evaluar(expresion: str) -> float:
    expr = _normalizar_expresion(expresion)
    if not expr:
        raise ValueError("expresion vacia")
    if len(expr) > 300:
        raise ValueError("expresion demasiado larga")
    if not re.fullmatch(r"[0-9a-zA-Z_+\-*/.()%]+", expr):
        raise ValueError(f"caracteres no permitidos en: {expr}")
    # Evitar que una sola letra 'e' se evalua por error si venia de basura
    if expr.lower() in _CONSTS and not re.search(r"\d|[+−\-*/]", expresion or ""):
        # Solo si el usuario escribio literalmente pi/e/tau
        if not re.search(rf"\b{re.escape(expr)}\b", expresion or "", re.I):
            if expr.lower() == "e":
                raise ValueError("expresion ambigua")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"sintaxis invalida: {expr}") from e
    return float(_SafeEval().visit(tree))


def _formatear_numero(x: float) -> str:
    if math.isnan(x):
        return "NaN"
    if math.isinf(x):
        return "∞" if x > 0 else "-∞"
    if abs(x - round(x)) < 1e-10 and abs(x) < 1e15:
        return str(int(round(x)))
    return f"{x:.12g}"


def resolver(texto: str, idioma: str = "es") -> Optional[str]:
    if not parece_calculo(texto):
        t = (texto or "").strip()
        if not re.search(r"\d", t):
            return None
        if not re.search(r"[+−\-*/^=%×÷√]|\b(por|entre|mas|menos)\b", t, re.I):
            return None

    try:
        expr_norm = _normalizar_expresion(texto)
        if not expr_norm or not re.search(r"\d", expr_norm):
            # Constante pura solo si el usuario la pidio
            if expr_norm.lower() not in _CONSTS:
                if idioma == "en":
                    return "I couldn't find a valid expression. Try 2+2 or sqrt(16)."
                return "No encontre una expresion valida. Prueba 2+2 o sqrt(16)."
        resultado = evaluar(texto)
        pretty = _formatear_numero(resultado)
        if idioma == "en":
            return f"Result: {pretty}\n(expression: {expr_norm})"
        return f"Resultado: {pretty}\n(expresión: {expr_norm})"
    except ZeroDivisionError:
        return (
            "No se puede dividir entre cero."
            if idioma != "en"
            else "Cannot divide by zero."
        )
    except ValueError as e:
        msg = str(e)
        if idioma == "en":
            return f"I couldn't compute that ({msg}). Try e.g. 2+2, sqrt(16), 15% de 80."
        return (
            f"No pude calcular eso ({msg}). "
            f"Prueba p. ej.: 2+2, sqrt(16), 15% de 80, sin(pi/2), factorial(5)."
        )
    except Exception as e:
        if idioma == "en":
            return f"Math error: {type(e).__name__}: {e}"
        return f"Error de calculo: {type(e).__name__}: {e}"


def formatear_ayuda(idioma: str = "es") -> str:
    if idioma == "en":
        return (
            "I can do math: 2+2, (3*4)/2, sqrt(16), 2**10, sin(pi/2), "
            "log(100), 15% of 80, factorial(6)."
        )
    return (
        "Puedo calcular: 2+2, (3*4)/2, sqrt(16), 2**10, sin(pi/2), "
        "log(100), 15% de 80, factorial(6), 3 elevado a 4."
    )
