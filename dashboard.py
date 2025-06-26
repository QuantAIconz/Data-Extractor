import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import os  # Ensure this is the correct import path for your environment

class DataVisualizer:
    def __init__(self, data):
        self.data = data
        self.df = pd.DataFrame(data)
        
    def create_distribution_chart(self):
        """Create a bar chart showing the distribution of data types."""
        # Count occurrences of each data type
        type_counts = self.df['type'].value_counts()
        
        fig = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            title='Distribution of Extracted Data Types',
            labels={'x': 'Data Type', 'y': 'Count'},
            color=type_counts.values,
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=500
        )
        
        return fig

    def create_file_distribution_chart(self):
        """Create a bar chart showing data distribution across files."""
        if 'filename' not in self.df.columns:
            # If no filename column, create a default one
            self.df['filename'] = 'Unknown File'
        
        file_counts = self.df['filename'].value_counts()
        
        fig = px.bar(
            x=file_counts.index,
            y=file_counts.values,
            title='Data Distribution Across Files',
            labels={'x': 'File Name', 'y': 'Number of Items'},
            color=file_counts.values,
            color_continuous_scale='Plasma'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=500
        )
        
        return fig

    def create_file_type_heatmap(self):
        """Create a heatmap showing data types vs files."""
        if 'filename' not in self.df.columns:
            self.df['filename'] = 'Unknown File'
        
        # Create a pivot table of files vs data types
        file_type_counts = pd.crosstab(self.df['filename'], self.df['type'])
        
        fig = px.imshow(
            file_type_counts,
            title='Data Types Distribution Across Files',
            labels=dict(x='Data Type', y='File Name', color='Count'),
            aspect='auto',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig

    def create_heatmap(self):
        """Create a heatmap showing data density by page number."""
        # Create a pivot table of page numbers vs data types
        page_type_counts = pd.crosstab(self.df['page'], self.df['type'])
        
        fig = px.imshow(
            page_type_counts,
            title='Data Density Heatmap by Page Number',
            labels=dict(x='Data Type', y='Page Number', color='Count'),
            aspect='auto',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig

    def create_validation_chart(self):
        """Create a pie chart showing validation status distribution."""
        status_counts = self.df['status'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Validation Status Distribution',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(height=500)
        return fig

    def create_file_validation_chart(self):
        """Create a stacked bar chart showing validation status by file."""
        if 'filename' not in self.df.columns:
            self.df['filename'] = 'Unknown File'
        
        # Create a pivot table of files vs validation status
        file_status_counts = pd.crosstab(self.df['filename'], self.df['status'])
        
        fig = px.bar(
            file_status_counts,
            title='Validation Status by File',
            labels={'value': 'Count', 'index': 'File Name'},
            barmode='stack'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig

    def create_timeline(self):
        """Create a timeline of data extraction."""
        # Add timestamp if not present
        if 'timestamp' not in self.df.columns:
            self.df['timestamp'] = datetime.now()
        
        # Group by timestamp and count
        timeline_data = self.df.groupby(self.df['timestamp'].dt.date).size().reset_index()
        timeline_data.columns = ['date', 'count']
        
        fig = px.line(
            timeline_data,
            x='date',
            y='count',
            title='Data Extraction Timeline',
            labels={'date': 'Date', 'count': 'Number of Extractions'}
        )
        
        fig.update_layout(height=500)
        return fig

    def create_correlation_matrix(self):
        """Create a correlation matrix between different data types."""
        # Create a binary matrix of data types
        type_matrix = pd.get_dummies(self.df['type'])
        
        # Calculate correlation
        correlation = type_matrix.corr()
        
        fig = px.imshow(
            correlation,
            title='Correlation Between Data Types',
            labels=dict(x='Data Type', y='Data Type', color='Correlation'),
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        
        fig.update_layout(height=500)
        return fig

    def create_summary_stats(self):
        """Create summary statistics cards."""
        total_items = len(self.df)
        valid_items = len(self.df[self.df['status'] == 'correct'])
        invalid_items = total_items - valid_items
        unique_files = self.df['filename'].nunique() if 'filename' in self.df.columns else 1
        unique_types = self.df['type'].nunique()
        
        # Calculate success rate
        success_rate = (valid_items / total_items * 100) if total_items > 0 else 0
        
        return {
            'total_items': total_items,
            'valid_items': valid_items,
            'invalid_items': invalid_items,
            'unique_files': unique_files,
            'unique_types': unique_types,
            'success_rate': round(success_rate, 2)
        }

    def generate_dashboard(self):
        """Generate all visualizations and return them as a dictionary."""
        dashboard = {
            'distribution': self.create_distribution_chart(),
            'heatmap': self.create_heatmap(),
            'validation': self.create_validation_chart(),
            'timeline': self.create_timeline(),
            'correlation': self.create_correlation_matrix()
        }
        
        # Add file-based visualizations if filename data is available
        if 'filename' in self.df.columns:
            dashboard['file_distribution'] = self.create_file_distribution_chart()
            dashboard['file_type_heatmap'] = self.create_file_type_heatmap()
            dashboard['file_validation'] = self.create_file_validation_chart()
        
        return dashboard

    def export_dashboard(self, output_dir='static/dashboard'):
        """Export all visualizations as HTML files."""
        os.makedirs(output_dir, exist_ok=True)
        
        dashboard = self.generate_dashboard()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export each visualization
        for name, fig in dashboard.items():
            filename = f'{output_dir}/{name}_{timestamp}.html'
            fig.write_html(filename)
        
        # Create an index file that combines all visualizations
        with open(f'{output_dir}/index_{timestamp}.html', 'w') as f:
            f.write('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Data Extraction Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .chart-container { margin-bottom: 30px; }
                    .summary-cards { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; }
                    .card { background: #f8f9fa; padding: 20px; border-radius: 8px; min-width: 150px; text-align: center; }
                    .card h3 { margin: 0; color: #007bff; }
                    .card p { margin: 5px 0; font-size: 24px; font-weight: bold; }
                    iframe { width: 100%; height: 600px; border: none; }
                </style>
            </head>
            <body>
                <h1>Data Extraction Dashboard</h1>
            ''')
            
            # Add summary statistics
            stats = self.create_summary_stats()
            f.write('''
                <div class="summary-cards">
                    <div class="card">
                        <h3>Total Items</h3>
                        <p>''' + str(stats['total_items']) + '''</p>
                    </div>
                    <div class="card">
                        <h3>Valid Items</h3>
                        <p>''' + str(stats['valid_items']) + '''</p>
                    </div>
                    <div class="card">
                        <h3>Success Rate</h3>
                        <p>''' + str(stats['success_rate']) + '''%</p>
                    </div>
                    <div class="card">
                        <h3>Files Processed</h3>
                        <p>''' + str(stats['unique_files']) + '''</p>
                    </div>
                    <div class="card">
                        <h3>Data Types</h3>
                        <p>''' + str(stats['unique_types']) + '''</p>
                    </div>
                </div>
            ''')
            
            for name in dashboard.keys():
                f.write(f'''
                <div class="chart-container">
                    <h2>{name.replace("_", " ").title()}</h2>
                    <iframe src="{name}_{timestamp}.html"></iframe>
                </div>
                ''')
            
            f.write('</body></html>')
        
        return f'{output_dir}/index_{timestamp}.html' 