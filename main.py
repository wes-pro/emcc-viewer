import collections
from flask import Flask, g
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import db
import config

emcc_db = db.OMRdb(config.db_user, config.db_pass, config.db_tns, config.target_types)
emcc_targets = emcc_db.get_targets()


def get_data_series():
    d = getattr(g, '_data_servies', None)
    if d is None:
        d = g._data_series = collections.OrderedDict()
    return d

#data_series = collections.OrderedDict()
#data_series_stacked = collections.OrderedDict()
add_clicks = 0
rem_clicks = 0
clear_clicks = 0

flask_app = Flask(__name__)
app = dash.Dash(__name__, server=flask_app)
#app = dash.Dash()

app.title = 'Plotly Dash and Oracle Enterprise Manager demo application'
app.layout = html.Div([

    html.Div([
        html.Div([
            html.H4('Plotly Dash and Oracle Enterprise Manager', className='display-6'),
            html.P('''
            How to use Dash framework to visualize performance data from Enterprise Manager Cloud Control
            ''', className='lead')
        ], className='container')
    ], className='jumbotron jumbotron-fluid', style={'height': '80px', 'padding': '0.5rem'}),

    html.Div([
        html.Div([
            html.Div([
                html.Label('Target:'),
                dcc.Dropdown(
                    id='target',
                    options=[{'label': d[0] + ' (' + config.target_typenames_map[d[1]] + ')', 'value': i} for i, d in emcc_targets.iterrows()]
                )
            ], className='col small'),
            html.Div([
                html.Label('Metric:'),
                dcc.Dropdown(
                    id='metric',
                )
            ], className='col small'),
            html.Div([
                html.Label('Metric column:'),
                dcc.Dropdown(
                    id='column',
                )
            ], className='col-lg small'),
            html.Div([
                html.Label('Stacked:'),
                dcc.Dropdown(
                    id='stacked',
                    options=[
                        {'label': 'Yes', 'value': True},
                        {'label': 'No', 'value': False}
                    ],
                    value=False
                )
            ], className='col col-1 small'),
            html.Div([
                html.Label('Y-factor:'),
                dcc.Input(id='factor', type='text', value='1', style={'width': '50px'}),
            ], className='col col-1 small'),
            html.Div([
                html.Div([
                    html.Button(id='add', children='Add', className='btn btn-primary btn-sm mr-1 mb-2'),
                    html.Button(id='rem', children='Remove', className='btn btn-primary btn-sm mr-1 mb-2'),
                    html.Button(id='clear', children='Clear', className='btn btn-primary btn-sm mb-2'),
                ], className='d-flex flex-raw h-100 align-items-end float-right')
            ], className='col-2 mx-auto')
        ], className='row mb-2'),
        html.Details([
            html.Summary('Advanced:', style={}),
            html.Div([
                html.Div([
                    html.Label('Resample?', className='mr-1'),
                    dcc.Checklist(id='resample', options=[{'value': True}], values=[])
                ], className="form-group col-2"),
                html.Div([
                    html.Label('Resample frequency:', className='mr-2'),
                    dcc.Input(id='frequency', value='10min', type='text', style={'width': '150px'}),
                ], className='form-group col-3 mr-4'),
                html.Div([
                    html.Label('Resample method:', className='mr-2'),
                    dcc.Dropdown(
                        id='method',
                        options=[
                            {'label': 'bfill', 'value': 'bfill'},
                            {'label': 'ffill', 'value': 'ffill'},
                            {'label': 'mean', 'value': 'mean'},
                            {'label': 'median', 'value': 'median'},
                        ],
                        value='bfill',
                    )
                ], className='form-group col-3 mr-4'),
            ], className='row form-inline mx-auto mb-4'),
        ], className='container-fluid'),
        html.Div([
            html.Div([
                dcc.Graph(id='graph')
            ], className='container-fluid')
        ], className='row border border-dark rounded ml-2 mr-2 mb-2'),
    ], className='container-fluid')
], id='page-content-wrapper ml-2 mr-2')

app.css.append_css({
    'external_url': 'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css'
})


@app.callback(
    Output('metric', 'options'),
    [Input('target', 'value')]
)
def get_metric_dropdown_options(target_guid):
    metrics = emcc_db.get_target_metrics(target_guid)
    options = [{'label': d[0], 'value': i} for i, d in metrics.iterrows()]
    return options

@app.callback(
    Output('column', 'options'),
    [Input('target', 'value'), Input('metric', 'value')]
)
def get_metric_dropdown_options(target_guid, metric):
    metrics = emcc_db.get_target_metric_columns(target_guid, metric)
    options = [{'label': d[0], 'value': i} for i, d in metrics.iterrows()]
    return options

@app.callback(
    Output('graph', 'figure'),
    [Input('add', 'n_clicks'),
     Input('rem', 'n_clicks'),
     Input('clear', 'n_clicks')],
    [State('target', 'value'),
     State('metric', 'value'),
     State('column', 'value'),
     State('factor', 'value'),
     State('stacked', 'value'),
     State('resample', 'values'),
     State('frequency', 'value'),
     State('method', 'value')]
)
def add_series(a_clicks, r_clicks, c_clicks, target_guid, metric, column, factor, stacked, resample, frequency, method):
    global add_clicks
    global rem_clicks
    global clear_clicks
    #global data_series
    #global data_series_stacked

    if c_clicks and c_clicks > clear_clicks:
        clear_clicks = c_clicks
        data_series.clear()
        data_series_stacked.clear()

    if a_clicks and a_clicks > add_clicks:
        add_clicks = a_clicks
        if resample:
            series = emcc_db.get_metric_column_data(target_guid, metric, column, frequency, method)
        else:
            series = emcc_db.get_metric_column_data(target_guid, metric, column)
        series.VALUE = series.VALUE * float(factor)
        if stacked:
            if data_series_stacked:
                last_series = next(reversed(data_series_stacked.values()))
                data_series_stacked[(target_guid, metric, column, factor)] = series.add(last_series, fill_value=0)
            else:
                data_series_stacked[(target_guid, metric, column, factor)] = series
        else:
            data_series[(target_guid, metric, column, factor)] = series

    if r_clicks and r_clicks > rem_clicks:
        rem_clicks = r_clicks
        if (target_guid, metric, column, factor) in data_series:
            del data_series[(target_guid, metric, column, factor)]
        if (target_guid, metric, column, factor) in data_series_stacked:
            del data_series_stacked[(target_guid, metric, column, factor)]

    simple_plots = [
        go.Scatter(
            x=data.index,
            y=data.VALUE,
            mode='lines+markers',
            #line=dict(dash='dot'),
            connectgaps=True,
            fill='none',
            name='{0} x {2} ({1})'.format(idx[2], emcc_targets.loc[idx[0]][0], idx[3])
        ) for idx, data in data_series.items()
    ]

    stacked_plots = [
        go.Scatter(
            x=data.index,
            y=data.VALUE,
            mode='lines+markers',
            connectgaps=True,
            fill='tonexty',
            name='{0} x {2} ({1})'.format(idx[2], emcc_targets.loc[idx[0]][0], idx[3])
        ) for idx, data in data_series_stacked.items()
    ]

    return go.Figure(
        data=stacked_plots + simple_plots,
        layout=go.Layout(
            showlegend=True,
            legend=dict(orientation='h', x=0, y=1),
            margin=dict(t=30, b=30, l=40, r=20),
            xaxis=dict(
                rangeslider=dict()
            )
        )
    )

if __name__ == '__main__':
    app.run_server(port=8999, debug=True)



