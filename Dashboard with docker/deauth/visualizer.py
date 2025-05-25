#!/usr/bin/env python3
"""
Deauth Attack Visualizer
Generates real-time visualization of deauthentication attacks
"""

import MySQLdb
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import os
import argparse
from collections import defaultdict, Counter

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard'
}

class DeauthVisualizer:
    def __init__(self, hours=1, output_dir=None):
        self.hours = hours
        self.output_dir = output_dir
        
        # Create output directory if specified
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Initialize data containers
        self.attacks = []
        self.attack_times = []
        self.attackers = Counter()
        self.targets = Counter()
        self.hourly_data = defaultdict(int)
        
        # Initialize plots
        self.fig, self.axs = plt.subplots(2, 2, figsize=(15, 10))
        self.fig.suptitle(f'Deauthentication Attack Analysis - Last {self.hours} Hours', fontsize=16)
        
        # Set up subplots
        self.timeline_ax = self.axs[0, 0]
        self.attackers_ax = self.axs[0, 1]
        self.targets_ax = self.axs[1, 0]
        self.hourly_ax = self.axs[1, 1]
        
        self.setup_plots()
    
    def setup_plots(self):
        """Set up the initial empty plots"""
        # Timeline plot
        self.timeline_ax.set_title('Attack Timeline')
        self.timeline_ax.set_xlabel('Time')
        self.timeline_ax.set_ylabel('Attack Count')
        self.timeline_ax.grid(True, linestyle='--', alpha=0.7)
        
        # Top attackers bar chart
        self.attackers_ax.set_title('Top Attackers')
        self.attackers_ax.set_xlabel('BSSID')
        self.attackers_ax.set_ylabel('Attack Count')
        
        # Top targets bar chart
        self.targets_ax.set_title('Top Targets')
        self.targets_ax.set_xlabel('BSSID')
        self.targets_ax.set_ylabel('Attack Count')
        
        # Hourly distribution bar chart
        self.hourly_ax.set_title('Hourly Attack Distribution')
        self.hourly_ax.set_xlabel('Hour')
        self.hourly_ax.set_ylabel('Attack Count')
        self.hourly_ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Improve layout
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])
    
    def get_attacks(self):
        """Fetch attack data from the database"""
        try:
            conn = MySQLdb.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Calculate time threshold
            time_threshold = datetime.now() - timedelta(hours=self.hours)
            
            # Query for attacks in time range
            query = """
                SELECT timestamp, alert_type, attacker_bssid, destination_bssid, attack_count
                FROM network_attacks
                WHERE timestamp >= %s
                ORDER BY timestamp
            """
            
            cursor.execute(query, (time_threshold,))
            results = cursor.fetchall()
            
            conn.close()
            
            # Process results
            self.attacks = []
            self.attack_times = []
            self.attackers = Counter()
            self.targets = Counter()
            self.hourly_data = defaultdict(int)
            
            for attack in results:
                timestamp, alert_type, attacker_bssid, target_bssid, count = attack
                
                self.attacks.append({
                    'timestamp': timestamp,
                    'alert_type': alert_type,
                    'attacker_bssid': attacker_bssid or 'Unknown',
                    'target_bssid': target_bssid or 'Unknown',
                    'count': count or 1
                })
                
                self.attack_times.append(timestamp)
                self.attackers[attacker_bssid or 'Unknown'] += 1
                self.targets[target_bssid or 'Unknown'] += 1
                self.hourly_data[timestamp.hour] += 1
            
            return len(self.attacks) > 0
            
        except Exception as e:
            print(f"Error fetching attack data: {e}")
            return False
    
    def update_timeline(self):
        """Update the timeline plot"""
        self.timeline_ax.clear()
        self.timeline_ax.set_title('Attack Timeline')
        self.timeline_ax.set_xlabel('Time')
        self.timeline_ax.set_ylabel('Attack Count')
        
        if self.attack_times:
            # Create histogram data
            bins = np.linspace(
                min(self.attack_times),
                max(self.attack_times) if self.attack_times else datetime.now(),
                20
            )
            
            self.timeline_ax.hist(self.attack_times, bins=bins, color='skyblue', edgecolor='blue')
            self.timeline_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            if len(self.attack_times) > 1:
                self.timeline_ax.set_xlim([min(self.attack_times), max(self.attack_times)])
        
        self.timeline_ax.grid(True, linestyle='--', alpha=0.7)
    
    def update_attackers(self):
        """Update the top attackers bar chart"""
        self.attackers_ax.clear()
        self.attackers_ax.set_title('Top Attackers')
        self.attackers_ax.set_xlabel('BSSID')
        self.attackers_ax.set_ylabel('Attack Count')
        
        top_attackers = self.attackers.most_common(5)
        
        if top_attackers:
            labels = [self.format_mac(a[0]) for a in top_attackers]
            values = [a[1] for a in top_attackers]
            
            bars = self.attackers_ax.bar(labels, values, color='lightcoral')
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                self.attackers_ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.1,
                    f'{int(height)}',
                    ha='center', va='bottom'
                )
            
            self.attackers_ax.set_xticklabels(labels, rotation=45, ha='right')
    
    def update_targets(self):
        """Update the top targets bar chart"""
        self.targets_ax.clear()
        self.targets_ax.set_title('Top Targets')
        self.targets_ax.set_xlabel('BSSID')
        self.targets_ax.set_ylabel('Attack Count')
        
        top_targets = self.targets.most_common(5)
        
        if top_targets:
            labels = [self.format_mac(t[0]) for t in top_targets]
            values = [t[1] for t in top_targets]
            
            bars = self.targets_ax.bar(labels, values, color='lightgreen')
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                self.targets_ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.1,
                    f'{int(height)}',
                    ha='center', va='bottom'
                )
            
            self.targets_ax.set_xticklabels(labels, rotation=45, ha='right')
    
    def update_hourly(self):
        """Update the hourly distribution bar chart"""
        self.hourly_ax.clear()
        self.hourly_ax.set_title('Hourly Attack Distribution')
        self.hourly_ax.set_xlabel('Hour')
        self.hourly_ax.set_ylabel('Attack Count')
        
        if self.hourly_data:
            hours = list(range(24))
            counts = [self.hourly_data[hour] for hour in hours]
            
            bars = self.hourly_ax.bar(hours, counts, color='lightskyblue')
            
            # Add value labels for non-zero bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    self.hourly_ax.text(
                        bar.get_x() + bar.get_width()/2.,
                        height + 0.1,
                        f'{int(height)}',
                        ha='center', va='bottom'
                    )
            
            self.hourly_ax.set_xticks(range(0, 24, 2))
            self.hourly_ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)])
        
        self.hourly_ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    def update_plots(self, frame):
        """Update all plots with the latest data"""
        if self.get_attacks():
            self.update_timeline()
            self.update_attackers()
            self.update_targets()
            self.update_hourly()
            
            # Update title with count information
            self.fig.suptitle(
                f'Deauthentication Attack Analysis - Last {self.hours} Hours\n'
                f'Total Attacks: {len(self.attacks)} | Unique Attackers: {len(self.attackers)} | Unique Targets: {len(self.targets)}',
                fontsize=16
            )
        
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])
        return self.axs
    
    def save_plots(self):
        """Save the current plots to files"""
        if not self.output_dir:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save combined figure
        plt.savefig(os.path.join(self.output_dir, f'deauth_analysis_{timestamp}.png'), dpi=300, bbox_inches='tight')
        
        # Save individual plots
        plt.figure(figsize=(10, 6))
        
        # Timeline
        plt.clf()
        self.update_timeline()
        plt.title('Attack Timeline', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'deauth_timeline_{timestamp}.png'), dpi=300, bbox_inches='tight')
        
        # Attackers
        plt.clf()
        self.update_attackers()
        plt.title('Top Attackers', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'deauth_attackers_{timestamp}.png'), dpi=300, bbox_inches='tight')
        
        # Targets
        plt.clf()
        self.update_targets()
        plt.title('Top Targets', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'deauth_targets_{timestamp}.png'), dpi=300, bbox_inches='tight')
        
        # Hourly
        plt.clf()
        self.update_hourly()
        plt.title('Hourly Attack Distribution', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'deauth_hourly_{timestamp}.png'), dpi=300, bbox_inches='tight')
        
        print(f"Plots saved to {self.output_dir}")
    
    @staticmethod
    def format_mac(mac):
        """Format MAC address for display"""
        if len(mac) > 10:
            return mac[:8] + '...'
        return mac
    
    def run_realtime(self, interval=5000):
        """Run the visualizer in real-time mode"""
        ani = FuncAnimation(self.fig, self.update_plots, interval=interval)
        plt.show()
    
    def run_static(self):
        """Run the visualizer in static mode"""
        self.update_plots(0)
        
        if self.output_dir:
            self.save_plots()
        
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='Deauthentication Attack Visualizer')
    parser.add_argument('--hours', type=int, default=1, help='Number of hours to analyze')
    parser.add_argument('--output', type=str, help='Directory to save plots')
    parser.add_argument('--static', action='store_true', help='Generate static plots instead of real-time')
    parser.add_argument('--interval', type=int, default=5000, help='Update interval in milliseconds for real-time mode')
    
    args = parser.parse_args()
    
    visualizer = DeauthVisualizer(hours=args.hours, output_dir=args.output)
    
    if args.static:
        visualizer.run_static()
    else:
        visualizer.run_realtime(interval=args.interval)

if __name__ == "__main__":
    main()
