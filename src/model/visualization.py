"""Visualization utilities for race calendar results."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional


def create_race_map(sequence_df, circuits_df, title = "Optimized F1 Race Calendar", output_path = None):
    """Create interactive map visualization of race calendar"""
    fig = go.Figure()
    
    # Add circuit markers for all circuits
    fig.add_trace(go.Scattergeo(
        lat=circuits_df['latitude'],
        lon=circuits_df['longitude'],
        text=circuits_df['circuit_name'],
        mode='markers',
        marker=dict(
            size=8,
            color='lightblue',
            line=dict(width=1, color='black')
        ),
        name='All Circuits',
        showlegend=True
    ))
    
    # Add race route lines
    for i in range(len(sequence_df) - 1):
        curr = sequence_df.iloc[i]
        next_race = sequence_df.iloc[i + 1]
        
        # Determine line color based on position
        if curr['position'] == 1:
            color = 'green'
            width = 4
        elif curr['position'] == len(sequence_df):
            color = 'red'
            width = 4
        else:
            color = 'blue'
            width = 2
        
        fig.add_trace(go.Scattergeo(
            lat=[curr['latitude'], next_race['latitude']],
            lon=[curr['longitude'], next_race['longitude']],
            mode='lines',
            line=dict(color=color, width=width),
            name=f"{curr['circuit_id']} → {next_race['circuit_id']}",
            showlegend=(i < 5),  # Show legend for first few routes
            opacity=0.8
        ))
    
    # Add race markers for scheduled races
    fig.add_trace(go.Scattergeo(
        lat=sequence_df['latitude'],
        lon=sequence_df['longitude'],
        text=sequence_df['circuit_name'],
        mode='markers+text',
        marker=dict(
            size=12,
            color='orange',
            line=dict(width=2, color='darkorange')
        ),
        name='Scheduled Races',
        showlegend=True,
        textposition='top right'
    ))
    
    # Layout configuration
    fig.update_layout(
        title=title,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor='black',
            coastlinewidth=0.5,
            projection_type='equirectangular',
            landcolor='rgb(217, 217, 217)',
            oceancolor='rgb(214, 229, 242)',
            showland=True,
            showocean=True,
            lataxis=dict(range=[-60, 80]),
            lonaxis=dict(range=[-180, 180])
        ),
        showlegend=True,
        height=700,
        width=1200
    )
    
    if output_path:
        fig.write_html(output_path)
    
    return fig


def create_gantt_chart(sequence_df, title = "F1 Race Calendar Schedule", output_path = None):
    """Create Gantt chart visualization of race calendar"""
    fig = go.Figure()
    
    for _, row in sequence_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['race_date']],
            y=[row['circuit_id']],
            mode='markers',
            marker=dict(
                size=15,
                color=row['position'],
                colorscale='Viridis',
                showscale=False,
                line=dict(width=2, color='darkblue')
            ),
            text=f"{row['circuit_name']}<br>Week {row['weekend']}",
            hoverinfo='text',
            name=row['circuit_id']
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Race Date",
        yaxis_title="Circuit",
        height=600,
        width=1000,
        showlegend=False
    )
    
    if output_path:
        fig.write_html(output_path)
    
    return fig


def create_emissions_breakdown(emissions_dict, title = "Emissions Breakdown", output_path = None):
    """Create pie chart of emissions breakdown"""
    labels = list(emissions_dict.keys())
    values = list(emissions_dict.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textinfo='label+percent',
        hoverinfo='label+value'
    )])
    
    fig.update_layout(
        title=title,
        showlegend=True
    )
    
    if output_path:
        fig.write_html(output_path)
    
    return fig
