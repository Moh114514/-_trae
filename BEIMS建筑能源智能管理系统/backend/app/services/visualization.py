import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Dict, Optional, Any, Union
import io
import base64
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class VisualizationService:
    def __init__(self):
        self.color_palettes = {
            'default': [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ],
            'warm': [
                '#ff9999', '#ffcc99', '#ffff99', '#99ff99', '#99ccff',
                '#cc99ff', '#ff99cc', '#ff6666', '#ffcc66', '#99ffcc'
            ],
            'cool': [
                '#6699ff', '#66ffff', '#66ff99', '#ff6666', '#ff9966',
                '#ffff66', '#99ff66', '#66ffcc', '#cc99ff', '#ff66cc'
            ],
            'business': [
                '#003366', '#0066cc', '#3399ff', '#66b3ff', '#99ccff',
                '#cc6600', '#ff9933', '#ffcc66', '#ffff99', '#ccffcc'
            ]
        }
        self.themes = {
            'light': 'plotly_white',
            'dark': 'plotly_dark',
            'presentation': 'presentation',
            'simple': 'simple_white',
            'seaborn': 'seaborn'
        }
    
    def create_line_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        title: str = "折线图",
        x_label: str = "",
        y_label: str = "",
        color_palette: str = "default",
        theme: str = "light",
        interactive: bool = True,
        show_legend: bool = True,
        annotations: Optional[List[Dict]] = None,
        range_x: Optional[List[Union[str, float]]] = None,
        range_y: Optional[List[float]] = None
    ) -> Dict:
        df = pd.DataFrame(data)
        
        colors = self.color_palettes.get(color_palette, self.color_palettes['default'])
        template = self.themes.get(theme, self.themes['light'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x_field],
            y=df[y_field],
            mode='lines+markers',
            name=y_field,
            line=dict(color=colors[0], width=2),
            marker=dict(size=6, hoveron='points'),
            hovertemplate=f'{x_field}: %{{x}}<br>{y_field}: %{{y}}<extra></extra>'
        ))
        
        layout_updates = {
            'title': title,
            'xaxis_title': x_label or x_field,
            'yaxis_title': y_label or y_field,
            'hovermode': 'x unified' if interactive else 'closest',
            'template': template,
            'showlegend': show_legend,
            'legend': dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if show_legend else None
        }
        
        if range_x:
            layout_updates['xaxis'] = {'range': range_x}
        if range_y:
            layout_updates['yaxis'] = {'range': range_y}
        
        if annotations:
            layout_updates['annotations'] = annotations
        
        fig.update_layout(**layout_updates)
        
        # 添加交互功能
        if interactive:
            fig.update_layout(
                margin=dict(l=50, r=50, t=50, b=50),
                height=400,
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )
        
        return json.loads(fig.to_json())
    
    def create_multi_line_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_fields: List[str],
        title: str = "多线折线图",
        x_label: str = "",
        y_label: str = "",
        color_palette: str = "default",
        theme: str = "light",
        interactive: bool = True,
        show_legend: bool = True,
        annotations: Optional[List[Dict]] = None,
        range_x: Optional[List[Union[str, float]]] = None,
        range_y: Optional[List[float]] = None
    ) -> Dict:
        df = pd.DataFrame(data)
        
        colors = self.color_palettes.get(color_palette, self.color_palettes['default'])
        template = self.themes.get(theme, self.themes['light'])
        
        fig = go.Figure()
        
        for i, y_field in enumerate(y_fields):
            fig.add_trace(go.Scatter(
                x=df[x_field],
                y=df[y_field],
                mode='lines+markers',
                name=y_field,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6, hoveron='points'),
                hovertemplate=f'{x_field}: %{{x}}<br>{y_field}: %{{y}}<extra></extra>'
            ))
        
        layout_updates = {
            'title': title,
            'xaxis_title': x_label or x_field,
            'yaxis_title': y_label or "数值",
            'hovermode': 'x unified' if interactive else 'closest',
            'template': template,
            'showlegend': show_legend,
            'legend': dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if show_legend else None
        }
        
        if range_x:
            layout_updates['xaxis'] = {'range': range_x}
        if range_y:
            layout_updates['yaxis'] = {'range': range_y}
        
        if annotations:
            layout_updates['annotations'] = annotations
        
        fig.update_layout(**layout_updates)
        
        # 添加交互功能
        if interactive:
            fig.update_layout(
                margin=dict(l=50, r=50, t=50, b=50),
                height=400,
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )
        
        return json.loads(fig.to_json())
    
    def create_animated_line_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        animation_field: str,
        title: str = "动画折线图",
        x_label: str = "",
        y_label: str = "",
        color_palette: str = "default",
        theme: str = "light"
    ) -> Dict:
        """创建动画折线图"""
        df = pd.DataFrame(data)
        
        colors = self.color_palettes.get(color_palette, self.color_palettes['default'])
        template = self.themes.get(theme, self.themes['light'])
        
        fig = px.line(
            df,
            x=x_field,
            y=y_field,
            animation_frame=animation_field,
            title=title,
            labels={x_field: x_label or x_field, y_field: y_label or y_field},
            template=template
        )
        
        fig.update_layout(
            margin=dict(l=50, r=50, t=50, b=50),
            height=400,
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        return json.loads(fig.to_json())
    
    def create_3d_scatter_plot(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        z_field: str,
        title: str = "3D散点图",
        color_field: Optional[str] = None,
        theme: str = "light"
    ) -> Dict:
        """创建3D散点图"""
        df = pd.DataFrame(data)
        
        template = self.themes.get(theme, self.themes['light'])
        
        fig = px.scatter_3d(
            df,
            x=x_field,
            y=y_field,
            z=z_field,
            color=color_field,
            title=title,
            template=template
        )
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            height=500,
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            )
        )
        
        return json.loads(fig.to_json())
    
    def create_polar_chart(
        self,
        data: List[Dict],
        r_field: str,
        theta_field: str,
        title: str = "极坐标图",
        color_field: Optional[str] = None,
        theme: str = "light"
    ) -> Dict:
        """创建极坐标图"""
        df = pd.DataFrame(data)
        
        template = self.themes.get(theme, self.themes['light'])
        
        fig = px.line_polar(
            df,
            r=r_field,
            theta=theta_field,
            color=color_field,
            title=title,
            template=template
        )
        
        fig.update_layout(
            margin=dict(l=50, r=50, t=50, b=50),
            height=400
        )
        
        return json.loads(fig.to_json())
    
    def export_chart(
        self,
        chart_json: Dict,
        format: str = "png",
        width: int = 1000,
        height: int = 600
    ) -> str:
        """导出图表为图片"""
        try:
            fig = go.Figure(chart_json)
            fig.update_layout(width=width, height=height)
            
            if format == "png":
                img_bytes = fig.to_image(format="png")
            elif format == "jpg":
                img_bytes = fig.to_image(format="jpg")
            elif format == "svg":
                img_bytes = fig.to_image(format="svg")
            elif format == "pdf":
                img_bytes = fig.to_image(format="pdf")
            else:
                img_bytes = fig.to_image(format="png")
            
            base64_encoded = base64.b64encode(img_bytes).decode('utf-8')
            return base64_encoded
        except Exception as e:
            logger.error(f"Export chart error: {str(e)}")
            return ""
    
    def get_chart_options(self) -> Dict:
        """获取图表选项"""
        return {
            "color_palettes": list(self.color_palettes.keys()),
            "themes": list(self.themes.keys()),
            "export_formats": ["png", "jpg", "svg", "pdf"],
            "chart_types": [
                "line", "multi_line", "bar", "grouped_bar", "stacked_bar",
                "pie", "donut", "area", "scatter", "heatmap", "histogram",
                "box", "gauge", "radar", "treemap", "waterfall", "funnel",
                "candlestick", "sunburst", "animated_line", "3d_scatter", "polar"
            ]
        }
    
    def create_bar_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        title: str = "柱状图",
        orientation: str = "v"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        if orientation == "v":
            fig.add_trace(go.Bar(
                x=df[x_field],
                y=df[y_field],
                marker_color=self.color_palette[0],
                text=df[y_field],
                textposition='auto'
            ))
        else:
            fig.add_trace(go.Bar(
                x=df[y_field],
                y=df[x_field],
                orientation='h',
                marker_color=self.color_palette[0],
                text=df[y_field],
                textposition='auto'
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_field if orientation == "v" else y_field,
            yaxis_title=y_field if orientation == "v" else x_field,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_grouped_bar_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_fields: List[str],
        title: str = "分组柱状图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        for i, y_field in enumerate(y_fields):
            fig.add_trace(go.Bar(
                x=df[x_field],
                y=df[y_field],
                name=y_field,
                marker_color=self.color_palette[i % len(self.color_palette)]
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_field,
            yaxis_title="数值",
            barmode='group',
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return json.loads(fig.to_json())
    
    def create_stacked_bar_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_fields: List[str],
        title: str = "堆叠柱状图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        for i, y_field in enumerate(y_fields):
            fig.add_trace(go.Bar(
                x=df[x_field],
                y=df[y_field],
                name=y_field,
                marker_color=self.color_palette[i % len(self.color_palette)]
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_field,
            yaxis_title="数值",
            barmode='stack',
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return json.loads(fig.to_json())
    
    def create_pie_chart(
        self,
        data: List[Dict],
        names_field: str,
        values_field: str,
        title: str = "饼图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure(data=[go.Pie(
            labels=df[names_field],
            values=df[values_field],
            hole=0.3,
            textinfo='label+percent',
            textposition='auto',
            marker=dict(colors=self.color_palette)
        )])
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_donut_chart(
        self,
        data: List[Dict],
        names_field: str,
        values_field: str,
        title: str = "环形图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure(data=[go.Pie(
            labels=df[names_field],
            values=df[values_field],
            hole=0.5,
            textinfo='label+percent',
            textposition='auto',
            marker=dict(colors=self.color_palette)
        )])
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_area_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_fields: List[str],
        title: str = "面积图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        for i, y_field in enumerate(y_fields):
            fig.add_trace(go.Scatter(
                x=df[x_field],
                y=df[y_field],
                fill='tozeroy' if i == 0 else 'tonexty',
                name=y_field,
                mode='lines',
                line=dict(color=self.color_palette[i % len(self.color_palette)], width=2)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_field,
            yaxis_title="数值",
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return json.loads(fig.to_json())
    
    def create_scatter_plot(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        title: str = "散点图",
        color_field: Optional[str] = None
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = px.scatter(
            df,
            x=x_field,
            y=y_field,
            color=color_field,
            title=title,
            template='plotly_white'
        )
        
        fig.update_traces(marker=dict(size=8, opacity=0.6))
        
        return json.loads(fig.to_json())
    
    def create_heatmap(
        self,
        data: List[List[float]],
        x_labels: List[str],
        y_labels: List[str],
        title: str = "热力图"
    ) -> Dict:
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=x_labels,
            y=y_labels,
            colorscale='RdYlBu_r'
        ))
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_histogram(
        self,
        data: List[float],
        title: str = "直方图",
        x_label: str = "数值",
        bins: int = 30
    ) -> Dict:
        fig = go.Figure(data=[go.Histogram(
            x=data,
            nbinsx=bins,
            marker_color=self.color_palette[0],
            opacity=0.75
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title="频数",
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_box_plot(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        title: str = "箱线图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        categories = df[x_field].unique()
        
        for i, category in enumerate(categories):
            fig.add_trace(go.Box(
                y=df[df[x_field] == category][y_field],
                name=str(category),
                marker_color=self.color_palette[i % len(self.color_palette)]
            ))
        
        fig.update_layout(
            title=title,
            yaxis_title=y_field,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_gauge_chart(
        self,
        value: float,
        title: str = "仪表盘",
        min_val: float = 0,
        max_val: float = 100,
        thresholds: Optional[List[float]] = None
    ) -> Dict:
        if thresholds is None:
            thresholds = [max_val * 0.33, max_val * 0.66]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [min_val, thresholds[0]], 'color': "lightgreen"},
                    {'range': [thresholds[0], thresholds[1]], 'color': "yellow"},
                    {'range': [thresholds[1], max_val], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        fig.update_layout(
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_radar_chart(
        self,
        data: List[Dict],
        categories_field: str,
        values_field: str,
        title: str = "雷达图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=df[values_field],
            theta=df[categories_field],
            fill='toself',
            name=values_field,
            line_color=self.color_palette[0]
        ))
        
        fig.update_layout(
            title=title,
            polar=dict(
                radialaxis=dict(
                    visible=True
                )
            ),
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_treemap(
        self,
        data: List[Dict],
        labels_field: str,
        values_field: str,
        parents_field: str = "",
        title: str = "树状图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        if parents_field and parents_field in df.columns:
            fig = go.Figure(go.Treemap(
                labels=df[labels_field],
                values=df[values_field],
                parents=df[parents_field],
                marker_colors=self.color_palette[:len(df)]
            ))
        else:
            fig = go.Figure(go.Treemap(
                labels=df[labels_field],
                values=df[values_field],
                marker_colors=self.color_palette[:len(df)]
            ))
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_waterfall_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        title: str = "瀑布图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Waterfall(
            x=df[x_field],
            y=df[y_field],
            measure=["relative"] * (len(df) - 1) + ["total"],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_funnel_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        title: str = "漏斗图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Funnel(
            y=df[y_field],
            x=df[x_field],
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(color=self.color_palette[:len(df)])
        ))
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_candlestick_chart(
        self,
        data: List[Dict],
        date_field: str,
        open_field: str,
        high_field: str,
        low_field: str,
        close_field: str,
        title: str = "K线图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure(data=[go.Candlestick(
            x=df[date_field],
            open=df[open_field],
            high=df[high_field],
            low=df[low_field],
            close=df[close_field]
        )])
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_sunburst_chart(
        self,
        data: List[Dict],
        labels_field: str,
        values_field: str,
        parents_field: str,
        title: str = "旭日图"
    ) -> Dict:
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Sunburst(
            labels=df[labels_field],
            values=df[values_field],
            parents=df[parents_field],
            marker=dict(colors=self.color_palette[:len(df)])
        ))
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_multi_subplot(
        self,
        charts: List[Dict],
        rows: int,
        cols: int,
        title: str = "多子图"
    ) -> Dict:
        fig = make_subplots(rows=rows, cols=cols, subplot_titles=[c.get('title', '') for c in charts])
        
        for i, chart in enumerate(charts):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            if chart['type'] == 'line':
                fig.add_trace(go.Scatter(
                    x=chart['data']['x'],
                    y=chart['data']['y'],
                    mode='lines+markers',
                    name=chart.get('name', f'Chart {i+1}')
                ), row=row, col=col)
            elif chart['type'] == 'bar':
                fig.add_trace(go.Bar(
                    x=chart['data']['x'],
                    y=chart['data']['y'],
                    name=chart.get('name', f'Chart {i+1}')
                ), row=row, col=col)
        
        fig.update_layout(
            title=title,
            template='plotly_white',
            showlegend=True
        )
        
        return json.loads(fig.to_json())
