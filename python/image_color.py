"""Decode source palettes with the desktop app's nearest-RGB inversion method."""
import math
import re
import numpy as np
from scipy.spatial import cKDTree
from palette_tables import BUILTIN_RGB

FIGURE_STOPS = [{'color': c, 'intensity': i/4} for i,c in enumerate(
    ['#ffffff','#ff0000','#ffff00','#00ff00','#0000ff'])]

def color_config(data):
    name = data.get('source_palette', 'luminance')
    if name not in ('luminance','figure','four_color','gray','custom',*BUILTIN_RGB):
        raise ValueError('Unknown source color scale.')
    reverse = data.get('palette_reverse', False)
    if not isinstance(reverse, bool):
        raise ValueError('Invalid color scale direction.')
    result = dict(source_palette=name, palette_reverse=reverse)
    if name == 'custom':
        stops = data.get('palette_stops', FIGURE_STOPS)
        if not isinstance(stops,list) or not 2 <= len(stops) <= 16:
            raise ValueError('Use between 2 and 16 color / intensity pairs.')
        method = data.get('palette_interpolation','linear')
        if method not in ('linear','nearest'):
            raise ValueError('Unknown color interpolation method.')
        checked=[]
        for stop in stops:
            if not isinstance(stop,dict) or not re.fullmatch(r'#[0-9a-fA-F]{6}',str(stop.get('color',''))):
                raise ValueError('Enter colors as #RRGGBB.')
            v=stop.get('intensity')
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1:
                raise ValueError('Color intensities must be between 0 and 1.')
            checked.append(dict(color=stop['color'].lower(),intensity=float(v)))
        if len({s['color'] for s in checked})!=len(checked):
            raise ValueError('Each color must occur only once in the scale.')
        checked.sort(key=lambda s:s['intensity'])
        if method=='linear' and len({s['intensity'] for s in checked})!=len(checked):
            raise ValueError('Interpolated scales need distinct intensity values. Use nearest colors for equal values.')
        result.update(palette_stops=checked,palette_interpolation=method)
    return result

def palette_table(config):
    name=config['source_palette']
    if name in BUILTIN_RGB:
        rgb=np.asarray(BUILTIN_RGB[name]); levels=np.linspace(0,1,len(rgb))
    else:
        stops=(config['palette_stops'] if name=='custom' else FIGURE_STOPS if name=='figure' else
               [{'color':c,'intensity':i/3} for i,c in enumerate(['#ffffff','#ffff00','#ff0000','#008000'])]
               if name=='four_color' else [{'color':'#000000','intensity':0},{'color':'#ffffff','intensity':1}])
        rgb=np.array([[int(s['color'][i:i+2],16)/255 for i in (1,3,5)] for s in stops])
        levels=np.array([s['intensity'] for s in stops])
        if name!='four_color' and config.get('palette_interpolation','linear')=='linear':
            # Keep the exact anchors as well as the dense interpolated path.
            axis=np.unique(np.r_[np.linspace(levels[0],levels[-1],2048),levels])
            rgb=np.column_stack([np.interp(axis,levels,rgb[:,i]) for i in range(3)])
            levels=axis
    if config['palette_reverse']:
        levels=1-levels
    return rgb,levels

def decode_intensity(source, data):
    values=np.asarray(source)
    if values.ndim==2:
        return values.astype(float), None, dict(source_palette='native',palette_reverse=False)
    config=color_config(data)
    if values.ndim!=3 or values.shape[2]!=3:
        raise ValueError('Unsupported image color channels.')
    flat=values.reshape(-1,3)
    out=np.empty(flat.shape[0],dtype=np.float32)
    distance=None
    if config['source_palette']!='luminance':
        rgb,levels=palette_table(config)
        tree=cKDTree(rgb)
        distance=np.empty(len(flat),dtype=np.float32)
    # Bounded scratch buffers, also for the largest permitted camera frames.
    for start in range(0,len(flat),65536):
        stop=min(start+65536,len(flat))
        block=flat[start:stop].astype(float)/255
        if config['source_palette']=='luminance':
            v=block @ np.array([.2126,.7152,.0722])
            out[start:stop]=1-v if config['palette_reverse'] else v
        else:
            d,index=tree.query(block,k=1,workers=1)
            out[start:stop]=levels[index];distance[start:stop]=d
    shape=values.shape[:2]
    return out.reshape(shape), None if distance is None else distance.reshape(shape), config
