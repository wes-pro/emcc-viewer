from collections import OrderedDict
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import db
import config

emcc_db = db.OMRdb(config.db_user, config.db_pass, config.db_tns, config.target_types)
emcc_targets = emcc_db.get_targets()

app = dash.Dash(name=__name__,static_folder='static')


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
    ], className='container-fluid'),
    html.Div(id='buttons_pressed', style={'display': 'none'}),
    html.Div(id='series_to_draw', style={'display': 'none'}),
], id='page-content-wrapper ml-2 mr-2')

app.css.append_css({'external_url': 'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css'})
app.css.append_css({'external_url': 'static/dash.css'})


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
    Output('buttons_pressed', 'children'),
    [Input('add', 'n_clicks'),
     Input('rem', 'n_clicks'),
     Input('clear', 'n_clicks')],
    [State('buttons_pressed', 'children')]
)
def press_button(n_clicks_add, n_clicks_rem, n_clicks_clear, buttons_pressed):
    if not n_clicks_add:
        n_clicks_add = 0
    if not n_clicks_rem:
        n_clicks_rem = 0
    if not n_clicks_clear:
        n_clicks_clear = 0

    curr_clicks = [str(x) for x in [n_clicks_add, n_clicks_rem, n_clicks_clear]]

    pressed = 'x'
    if buttons_pressed:
        prev_clicks = json.loads(buttons_pressed).split(';')
        for i in range(3):
            if prev_clicks[i] != curr_clicks[i]:
                pressed = i
                break

    output = ';'.join(str(x) for x in curr_clicks + [pressed])
    return json.dumps(output)


@app.callback(
    Output('series_to_draw', 'children'),
    [Input('buttons_pressed', 'children')],
    [State('target', 'value'),
     State('metric', 'value'),
     State('column', 'value'),
     State('factor', 'value'),
     State('stacked', 'value'),
     State('resample', 'values'),
     State('frequency', 'value'),
     State('method', 'value'),
     State('series_to_draw', 'children')]
)
def add_series(buttons_pressed, target_guid, metric, column, factor, stacked, resample, frequency, method, series_to_draw):
    button = json.loads(buttons_pressed).split(';')[3]

    if resample and resample[0]:
        resample = True
    else:
        resample = False
    series_list = OrderedDict()

    if button == '0':
        if series_to_draw:
            series_list = json.loads(series_to_draw, object_pairs_hook=OrderedDict)
        series_list[';'.join((target_guid, metric, column, factor))] = {'stacked': stacked,
                                                                        'resample': resample,
                                                                        'frequency': frequency,
                                                                        'method': method}

    if button == '1':
        if series_to_draw:
            series_list = json.loads(series_to_draw, object_pairs_hook=OrderedDict)
            del series_list[';'.join((target_guid, metric, column, factor))]

    if button == '2':
        series_list.clear()

    return json.dumps(series_list)


@app.callback(
    Output('graph', 'figure'),
    [Input('series_to_draw', 'children')]
)
def draw(series_to_draw):
    if series_to_draw:
        data_series = OrderedDict()
        data_series_stacked = OrderedDict()
        series_list = json.loads(series_to_draw, object_pairs_hook=OrderedDict)
        for idx, params in series_list.items():
            (target_guid, metric, column, factor) = idx.split(';')
            stacked = params['stacked']
            resample = params['resample']
            frequency = params['frequency']
            method = params['method']

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
                legend=dict(orientation='h', x=0, y=1.1),
                margin=dict(t=50, b=30, l=40, r=20),
                xaxis=dict(
                    rangeslider=dict()
                )
            )
        )

if __name__ == '__main__':
    app.run_server(port=8999, debug=True, host='0.0.0.0')



