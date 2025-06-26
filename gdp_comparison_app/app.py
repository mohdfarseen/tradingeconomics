from flask import Flask, render_template, request, send_file
import requests
import plotly.graph_objs as go
import plotly.io as pio
from urllib.parse import quote
import csv
import io

app = Flask(__name__)

API_KEY = '3c44373175494e3:smcek76y8uygfpx'

def get_gdp_data(country):
    try:
        encoded_country = quote(country)
        url = f"https://api.tradingeconomics.com/historical/country/{encoded_country}/indicator/gdp?c={API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data:
            return [], []

        unique_years_data = {}
        sorted_data = sorted(data, key=lambda x: x['DateTime'], reverse=True)

        for item in sorted_data:
            year = item['DateTime'][:4]
            if year not in unique_years_data:
                unique_years_data[year] = item['Value']

        if not unique_years_data:
            return [], []

        recent_years = sorted(unique_years_data.keys(), reverse=True)[:20]
        recent_years.reverse()

        values = [unique_years_data[year] for year in recent_years]

        return recent_years, values

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {country}: {e}")
        return [], []
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error processing data for {country}: {e}")
        return [], []

@app.route('/', methods=['GET', 'POST'])
def index():
    countries = ['sweden', 'mexico', 'new zealand', 'thailand']

    country1 = 'sweden'
    country2 = 'mexico'

    if request.method == 'POST':
        country1 = request.form.get('country1', 'sweden')
        country2 = request.form.get('country2', 'mexico')

    error_messages = []

    years1, gdp1 = get_gdp_data(country1)
    if not gdp1:
        error_messages.append(f"Data for {country1.title()} could not be retrieved. The API might be temporarily unavailable.")

    years2, gdp2 = get_gdp_data(country2)
    if not gdp2:
        error_messages.append(f"Data for {country2.title()} could not be retrieved. The API might be temporarily unavailable.")

    fig = go.Figure()

    if gdp1:
        fig.add_trace(go.Scatter(
            x=years1, y=gdp1, mode='lines+markers', name=country1.title(),
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8, symbol='circle', line=dict(width=1, color='DarkSlateGrey')),
            hovertemplate=f'<b>{country1.title()}</b><br>' + 'Year: %{x}<br>' + 'GDP: %{y:$,.2f}B<extra></extra>'
        ))

    if gdp2:
        fig.add_trace(go.Scatter(
            x=years2, y=gdp2, mode='lines+markers', name=country2.title(),
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8, symbol='circle', line=dict(width=1, color='DarkSlateGrey')),
            hovertemplate=f'<b>{country2.title()}</b><br>' + 'Year: %{x}<br>' + 'GDP: %{y:$,.2f}B<extra></extra>'
        ))

    fig.update_layout(
        title=dict(
            text=f'GDP Comparison: <b>{country1.title()}</b> vs <b>{country2.title()}</b>',
            y=0.9, x=0.5, xanchor='center', yanchor='top',
            font=dict(size=24, color='white', family='Arial, sans-serif')
        ),
        xaxis_title='Year', yaxis_title='GDP (in Billion USD)',
        font=dict(family="Arial, sans-serif", size=12, color="white"),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=14)),
        margin=dict(l=80, r=40, b=80, t=100)
    )

    chart_html = pio.to_html(fig, full_html=False, config={'displayModeBar': False})

    table_data = list(zip(years1, gdp1, gdp2)) if years1 == years2 else []

    return render_template('index.html', countries=sorted(countries), chart=chart_html,
                           selected1=country1, selected2=country2,
                           error_messages=error_messages, table_data=table_data,
                           country1=country1.title(), country2=country2.title())

@app.route('/download_csv')
def download_csv():
    country1 = request.args.get('country1', 'sweden')
    country2 = request.args.get('country2', 'mexico')

    years1, gdp1 = get_gdp_data(country1)
    years2, gdp2 = get_gdp_data(country2)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Year', country1.title(), country2.title()])

    if years1 == years2:
        for year, val1, val2 in zip(years1, gdp1, gdp2):
            writer.writerow([year, val1, val2])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='gdp_comparison.csv')

if __name__ == '__main__':
    app.run(debug=True)
