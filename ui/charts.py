"""Source-linked plots with explicit units and per-observation reference bands."""
import plotly.graph_objects as go


def lab_chart(observations, show_range=True, height=265):
    rows = sorted([o for o in observations if o.date and o.comparator == "=" and o.status in {"accepted", "corrected"}], key=lambda o: o.date)
    fig = go.Figure()
    if not rows:
        return fig
    x = [o.date for o in rows]
    if show_range and all(o.low is not None and o.high is not None for o in rows):
        fig.add_trace(go.Scatter(x=x, y=[o.high for o in rows], mode="lines",
            line=dict(width=0, shape="hv"), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=x, y=[o.low for o in rows], mode="lines",
            line=dict(width=0, shape="hv"), fill="tonexty", fillcolor="rgba(40,163,131,0.07)",
            name="Source reference range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=[o.value for o in rows], mode="lines+markers",
        name=rows[0].name, line=dict(color="#159885", width=3),
        marker=dict(size=8, color="#fff", line=dict(width=2, color="#159885")),
        customdata=[[o.unit, o.locator, o.document_id, o.low, o.high] for o in rows],
        hovertemplate="%{x|%d %b %Y}<br><b>%{y} %{customdata[0]}</b><br>Range: %{customdata[3]}–%{customdata[4]}<br>%{customdata[2]}<br>%{customdata[1]}<extra></extra>"))
    fig.update_layout(height=height, margin=dict(l=5, r=10, t=10, b=5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif", color="#7b8d99", size=10),
        showlegend=False, hovermode="x unified", dragmode=False,
        xaxis=dict(showgrid=False, tickformat="%b %y", tickmode="array", tickvals=x, zeroline=False),
        yaxis=dict(gridcolor="#edf1f4", zeroline=False, title=rows[0].unit))
    return fig

