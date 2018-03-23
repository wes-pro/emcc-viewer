import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import db
import config

emcc_db = db.OMRdb(config.db_user, config.db_pass, config.db_tns, config.target_types)
emcc_targets = emcc_db.get_targets()
emcc_metric = []
emcc_metric_columns = []
data_series = {}

add_clicks = 0

app = dash.Dash()

app.title = 'Dash and Oracle Enterprise Manager demo application'
app.layout = html.Div([

    html.Div([
        html.Div([
            html.H2('Dash and Oracle Enterprise Manager', className='display-6'),
            html.P('''
            How to use Dash framework to visualize performance data from Enterprise Manager Cloud Control
            ''', className='lead')
        ], className='container')
    ], className='jumbotron jumbotron-fluid mb-4'),

    html.Div([
        html.Div([
            html.Div([
                html.Label('Target:'),
                dcc.Dropdown(
                    id='target',
                    options=[{'label': d[0] + ' (' + d[1] + ')', 'value': i} for i, d in emcc_targets.iterrows()]
                )
            ], className='col-sm'),
            html.Div([
                html.Label('Metric:'),
                dcc.Dropdown(
                    id='metric',
                )
            ], className='col-sm'),
            html.Div([
                html.Label('Metric column:'),
                dcc.Dropdown(
                    id='column',
                )
            ], className='col-sm'),
            html.Div([
                html.Label('Y-factor:'),
                html.Div([
                    dcc.Input(id='factor', type='text', value='1'),
                ])
            ], className='col-sm'),
            html.Div([
                html.Div([
                    html.Button(id='add', children='Add', className='btn btn-primary btn-sm mr-2 mb-1'),
                    html.Button(id='rem', children='Remove', className='btn btn-primary btn-sm mb-1'),
                ], className='d-flex flex-raw h-100 align-items-end')
            ], className='col-sm')
        ], className='row'),
        html.Div([
            html.Div([
                dcc.Graph(id='graph')
            ], className='container-fluid')
        ], className='row'),
        html.Div([
            html.Label('Test output:'),
            html.Div(id='test_output')
        ], className='row', style={'display': 'none'})
    ], className='container-fluid')
], id='page-content-wrapper')

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
     Input('rem', 'n_clicks')],
    [State('target', 'value'),
     State('metric', 'value'),
     State('column', 'value'),
     State('factor', 'value')]
)
def add_series(a_clicks, r_clicks, target_guid, metric, column, factor):
    global add_clicks
    if not a_clicks:
        return None
    if a_clicks > add_clicks:
        series = emcc_db.get_metric_column_data(target_guid, metric, column)
        print(factor)
        series.VALUE = series.VALUE * float(factor)
        data_series[(target_guid, metric, column, factor)] = series
        add_clicks = a_clicks
    else:
        del data_series[(target_guid, metric, column, factor)]
    return go.Figure(
        data=[
            go.Scatter(
                x=data.index,
                y=data.VALUE,
                mode='lines',
                fill='tonexty',
                name='{0} x {2} ({1})'.format(idx[2], emcc_targets.loc[idx[0]][0], idx[3])
            ) for idx, data in data_series.items()
        ],
        layout=go.Layout(
            showlegend=True,
            legend=dict(orientation='h'),
            xaxis=dict(
                rangeslider=dict()
            )
        )
    )




if __name__ == '__main__':
    app.run_server(port=8999, debug=True)



