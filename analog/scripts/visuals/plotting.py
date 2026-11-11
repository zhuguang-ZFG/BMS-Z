"""Small plotting helpers; physical coordinates and layouts remain in each scene."""
from html import escape
from .primitives import Graphic, text
from .static_fig import paper_layers


def polyline(points, color, *, dash='', begin=None, duration=2, identity='trace'):
    pts=' '.join(f'{x:.4f},{y:.4f}' for x,y in points)
    curve=f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>'
    if begin is None:
        return curve
    left,right=min(x for x,_ in points),max(x for x,_ in points)
    top,bottom=min(y for _,y in points)-8,max(y for _,y in points)+8
    animated=(f'<defs><clipPath id="{identity}"><rect x="{left:g}" y="{top:g}" width="0" height="{bottom-top:g}">'
              f'<animate attributeName="width" from="0" to="{right-left:g}" begin="{begin:g}s" dur="{duration:g}s" fill="freeze"/>'
              f'</rect></clipPath></defs><g clip-path="url(#{identity})">{curve}</g>')
    return Graphic(animated,curve)


def print_header(title,height,description):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
            paper_layers(720,height),text(36,36,title,24)]
