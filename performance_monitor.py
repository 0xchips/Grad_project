#!/usr/bin/env python3
"""
Performance Monitor and System Optimizer for WiGuard Dashboard
Monitors system performance and provides optimization recommendations
"""

import os
import sys
import time
import psutil
import platform
import threading
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import subprocess
import signal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage_percent: float
    network_io: Dict
    process_count: int
    load_average: List[float]
    temperature: Optional[float] = None
    
@dataclass
class PerformanceAlert:
    timestamp: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'cpu', 'memory', 'disk', 'network', 'temperature'
    message: str
    value: float
    threshold: float
    recommendation: str

class PerformanceMonitor:
    """System performance monitoring and optimization"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.alerts = deque(maxlen=100)
        self.monitoring_active = False
        self.monitoring_thread = None
        self.callbacks = []
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': {'medium': 70, 'high': 85, 'critical': 95},
            'memory_percent': {'medium': 75, 'high': 90, 'critical': 95},
            'disk_usage_percent': {'medium': 80, 'high': 90, 'critical': 95},
            'temperature': {'medium': 70, 'high': 80, 'critical': 90},
            'load_average': {'medium': 2.0, 'high': 4.0, 'critical': 8.0}
        }
        
        # System info
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> Dict:
        """Get static system information"""
        info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': None,
            'memory_total': psutil.virtual_memory().total,
            'boot_time': psutil.boot_time(),
        }
        
        # Try to get CPU frequency
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                info['cpu_freq'] = {
                    'current': cpu_freq.current,
                    'min': cpu_freq.min,
                    'max': cpu_freq.max
                }
        except:
            pass
            
        return info
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        network_io = {}
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                network_io = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                }
        except:
            pass
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Linux/Unix only)
        load_average = []
        try:
            if hasattr(os, 'getloadavg'):
                load_average = list(os.getloadavg())
        except:
            pass
        
        # Temperature (if available)
        temperature = self._get_cpu_temperature()
        
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available=memory.available,
            disk_usage_percent=disk.percent,
            network_io=network_io,
            process_count=process_count,
            load_average=load_average,
            temperature=temperature
        )
        
        return metrics
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature if available"""
        try:
            # Try psutil sensors
            temps = psutil.sensors_temperatures()
            if temps:
                # Look for CPU temperature
                for name, entries in temps.items():
                    if 'cpu' in name.lower() or 'core' in name.lower():
                        if entries:
                            return entries[0].current
                            
                # Fallback to first available temperature
                first_sensor = next(iter(temps.values()))
                if first_sensor:
                    return first_sensor[0].current
        except:
            pass
            
        # Try reading from /sys/class/thermal (Linux)
        try:
            thermal_zone = Path('/sys/class/thermal/thermal_zone0/temp')
            if thermal_zone.exists():
                temp = int(thermal_zone.read_text().strip())
                return temp / 1000.0  # Convert from millidegrees
        except:
            pass
            
        return None
    
    def analyze_metrics(self, metrics: SystemMetrics) -> List[PerformanceAlert]:
        """Analyze metrics and generate alerts"""
        alerts = []
        
        # CPU analysis
        cpu_alert = self._check_threshold('cpu_percent', metrics.cpu_percent, 
                                         "High CPU usage detected")
        if cpu_alert:
            cpu_alert.recommendation = self._get_cpu_optimization_tips(metrics.cpu_percent)
            alerts.append(cpu_alert)
        
        # Memory analysis
        memory_alert = self._check_threshold('memory_percent', metrics.memory_percent,
                                           "High memory usage detected")
        if memory_alert:
            memory_alert.recommendation = self._get_memory_optimization_tips(metrics.memory_percent)
            alerts.append(memory_alert)
        
        # Disk analysis
        disk_alert = self._check_threshold('disk_usage_percent', metrics.disk_usage_percent,
                                         "High disk usage detected")
        if disk_alert:
            disk_alert.recommendation = self._get_disk_optimization_tips(metrics.disk_usage_percent)
            alerts.append(disk_alert)
        
        # Temperature analysis
        if metrics.temperature:
            temp_alert = self._check_threshold('temperature', metrics.temperature,
                                             "High system temperature detected")
            if temp_alert:
                temp_alert.recommendation = self._get_temperature_optimization_tips(metrics.temperature)
                alerts.append(temp_alert)
        
        # Load average analysis (if available)
        if metrics.load_average:
            avg_load = metrics.load_average[0]  # 1-minute average
            load_alert = self._check_threshold('load_average', avg_load,
                                             "High system load detected")
            if load_alert:
                load_alert.recommendation = self._get_load_optimization_tips(avg_load)
                alerts.append(load_alert)
        
        return alerts
    
    def _check_threshold(self, metric_name: str, value: float, message: str) -> Optional[PerformanceAlert]:
        """Check if value exceeds thresholds"""
        thresholds = self.thresholds.get(metric_name, {})
        
        severity = None
        threshold = None
        
        if value >= thresholds.get('critical', float('inf')):
            severity = 'critical'
            threshold = thresholds['critical']
        elif value >= thresholds.get('high', float('inf')):
            severity = 'high'
            threshold = thresholds['high']
        elif value >= thresholds.get('medium', float('inf')):
            severity = 'medium'
            threshold = thresholds['medium']
        
        if severity:
            return PerformanceAlert(
                timestamp=time.time(),
                severity=severity,
                category=metric_name.split('_')[0],
                message=f"{message}: {value:.1f}%",
                value=value,
                threshold=threshold,
                recommendation=""  # Will be filled by caller
            )
        
        return None
    
    def _get_cpu_optimization_tips(self, cpu_percent: float) -> str:
        """Get CPU optimization recommendations"""
        tips = []
        
        if cpu_percent > 90:
            tips.extend([
                "Consider reducing concurrent monitoring processes",
                "Check for runaway processes using 'top' or 'htop'",
                "Consider using lower scan frequencies"
            ])
        elif cpu_percent > 70:
            tips.extend([
                "Monitor system processes for unusual activity",
                "Consider optimizing scan intervals",
                "Check if multiple monitoring tools are running"
            ])
        
        return "; ".join(tips)
    
    def _get_memory_optimization_tips(self, memory_percent: float) -> str:
        """Get memory optimization recommendations"""
        tips = []
        
        if memory_percent > 90:
            tips.extend([
                "Clear system caches: 'sudo sync && echo 3 > /proc/sys/vm/drop_caches'",
                "Stop unnecessary services",
                "Consider increasing swap space",
                "Reduce packet capture buffer sizes"
            ])
        elif memory_percent > 75:
            tips.extend([
                "Monitor memory usage with 'free -h'",
                "Check for memory leaks in running processes",
                "Consider optimizing database queries"
            ])
        
        return "; ".join(tips)
    
    def _get_disk_optimization_tips(self, disk_percent: float) -> str:
        """Get disk optimization recommendations"""
        tips = []
        
        if disk_percent > 90:
            tips.extend([
                "Clean old log files: 'sudo journalctl --vacuum-time=7d'",
                "Remove unnecessary packages: 'sudo apt autoremove'",
                "Compress or archive old capture files",
                "Consider using log rotation"
            ])
        elif disk_percent > 80:
            tips.extend([
                "Monitor disk usage with 'df -h'",
                "Check large files with 'du -sh /*'",
                "Consider cleaning temporary files"
            ])
        
        return "; ".join(tips)
    
    def _get_temperature_optimization_tips(self, temperature: float) -> str:
        """Get temperature optimization recommendations"""
        tips = []
        
        if temperature > 85:
            tips.extend([
                "Check system cooling and ventilation",
                "Reduce CPU-intensive operations",
                "Consider thermal throttling protection",
                "Monitor system fans"
            ])
        elif temperature > 70:
            tips.extend([
                "Monitor temperature trends",
                "Ensure adequate ventilation",
                "Check for dust buildup in cooling systems"
            ])
        
        return "; ".join(tips)
    
    def _get_load_optimization_tips(self, load_average: float) -> str:
        """Get load average optimization recommendations"""
        cpu_count = self.system_info.get('cpu_count', 1)
        tips = []
        
        if load_average > cpu_count * 2:
            tips.extend([
                "System is heavily overloaded",
                "Consider reducing concurrent operations",
                "Check for I/O bottlenecks",
                "Monitor process queue with 'ps aux'"
            ])
        elif load_average > cpu_count:
            tips.extend([
                "System load is above optimal level",
                "Monitor running processes",
                "Consider process scheduling optimization"
            ])
        
        return "; ".join(tips)
    
    def start_monitoring(self, interval: int = 10, callback=None):
        """Start performance monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        if callback:
            self.callbacks.append(callback)
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Performance monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Analyze for alerts
                alerts = self.analyze_metrics(metrics)
                for alert in alerts:
                    self.alerts.append(alert)
                    logger.warning(f"Performance alert: {alert.message}")
                
                # Call callbacks
                for callback in self.callbacks:
                    try:
                        callback(metrics, alerts)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)
    
    def get_current_status(self) -> Dict:
        """Get current system status"""
        if not self.metrics_history:
            metrics = self.collect_metrics()
        else:
            metrics = self.metrics_history[-1]
        
        recent_alerts = [alert for alert in self.alerts 
                        if time.time() - alert.timestamp < 300]  # Last 5 minutes
        
        return {
            'timestamp': metrics.timestamp,
            'system_info': self.system_info,
            'current_metrics': asdict(metrics),
            'recent_alerts': [asdict(alert) for alert in recent_alerts],
            'performance_summary': self._get_performance_summary(),
            'optimization_recommendations': self._get_optimization_recommendations()
        }
    
    def _get_performance_summary(self) -> Dict:
        """Get performance summary over recent history"""
        if len(self.metrics_history) < 2:
            return {}
        
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 readings
        
        return {
            'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            'avg_disk_usage': sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics),
            'avg_temperature': sum((m.temperature or 0) for m in recent_metrics) / len(recent_metrics) if any(m.temperature for m in recent_metrics) else None,
            'trend_cpu': self._calculate_trend([m.cpu_percent for m in recent_metrics]),
            'trend_memory': self._calculate_trend([m.memory_percent for m in recent_metrics])
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 3:
            return 'stable'
        
        # Simple trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = ((second_half - first_half) / first_half) * 100
        
        if diff_percent > 10:
            return 'increasing'
        elif diff_percent < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Get system-wide optimization recommendations"""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        latest = self.metrics_history[-1]
        
        # System-specific recommendations
        if platform.system().lower() == 'linux':
            recommendations.extend(self._get_linux_optimizations(latest))
        
        # Wireless monitoring specific recommendations
        recommendations.extend(self._get_wireless_optimizations(latest))
        
        return recommendations
    
    def _get_linux_optimizations(self, metrics: SystemMetrics) -> List[str]:
        """Get Linux-specific optimizations"""
        optimizations = []
        
        if metrics.memory_percent > 80:
            optimizations.extend([
                "Enable swap if not available: 'sudo swapon -s'",
                "Tune kernel parameters: 'echo 1 > /proc/sys/vm/drop_caches'",
                "Consider using zram for compressed swap"
            ])
        
        if metrics.cpu_percent > 80:
            optimizations.extend([
                "Set CPU governor to performance: 'cpufreq-set -g performance'",
                "Check process nice values: 'ps -eo pid,comm,nice'",
                "Consider process affinity tuning"
            ])
        
        return optimizations
    
    def _get_wireless_optimizations(self, metrics: SystemMetrics) -> List[str]:
        """Get wireless monitoring specific optimizations"""
        optimizations = []
        
        optimizations.extend([
            "Optimize packet capture buffer sizes in real_time_monitor.py",
            "Consider reducing scan frequencies during high load",
            "Use monitor mode only when necessary",
            "Implement packet filtering to reduce processing load",
            "Consider database query optimization for large datasets"
        ])
        
        return optimizations
    
    def export_metrics(self, filepath: str, format: str = 'json'):
        """Export metrics history"""
        data = {
            'system_info': self.system_info,
            'metrics': [asdict(m) for m in self.metrics_history],
            'alerts': [asdict(a) for a in self.alerts],
            'export_timestamp': time.time()
        }
        
        with open(filepath, 'w') as f:
            if format.lower() == 'json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Metrics exported to {filepath}")

def main():
    """CLI interface for performance monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WiGuard Performance Monitor')
    parser.add_argument('--status', action='store_true', help='Show current system status')
    parser.add_argument('--monitor', type=int, metavar='INTERVAL', help='Start monitoring with interval (seconds)')
    parser.add_argument('--export', metavar='FILEPATH', help='Export metrics to file')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if args.status:
        status = monitor.get_current_status()
        
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("WiGuard System Performance Status")
            print("=" * 50)
            print(f"Platform: {status['system_info']['platform']}")
            print(f"CPU Count: {status['system_info']['cpu_count']}")
            print(f"Total Memory: {status['system_info']['memory_total'] / (1024**3):.1f} GB")
            print()
            
            metrics = status['current_metrics']
            print("Current Metrics:")
            print(f"  CPU Usage: {metrics['cpu_percent']:.1f}%")
            print(f"  Memory Usage: {metrics['memory_percent']:.1f}%")
            print(f"  Disk Usage: {metrics['disk_usage_percent']:.1f}%")
            if metrics['temperature']:
                print(f"  Temperature: {metrics['temperature']:.1f}°C")
            if metrics['load_average']:
                print(f"  Load Average: {metrics['load_average'][0]:.2f}")
            print()
            
            alerts = status['recent_alerts']
            if alerts:
                print("Recent Alerts:")
                for alert in alerts[-5:]:  # Show last 5 alerts
                    print(f"  [{alert['severity'].upper()}] {alert['message']}")
                    if alert['recommendation']:
                        print(f"    → {alert['recommendation']}")
            else:
                print("No recent alerts")
            print()
            
            recommendations = status['optimization_recommendations']
            if recommendations:
                print("Optimization Recommendations:")
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"  {i}. {rec}")
    
    elif args.monitor:
        print(f"Starting performance monitoring (interval: {args.monitor}s)")
        print("Press Ctrl+C to stop")
        
        def callback(metrics, alerts):
            timestamp = datetime.fromtimestamp(metrics.timestamp).strftime('%H:%M:%S')
            print(f"[{timestamp}] CPU: {metrics.cpu_percent:.1f}% | "
                  f"Memory: {metrics.memory_percent:.1f}% | "
                  f"Disk: {metrics.disk_usage_percent:.1f}%")
            
            for alert in alerts:
                print(f"  ALERT [{alert.severity.upper()}]: {alert.message}")
        
        monitor.start_monitoring(interval=args.monitor, callback=callback)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\nMonitoring stopped")
    
    elif args.export:
        # Collect some metrics first
        print("Collecting metrics for export...")
        for i in range(10):
            metrics = monitor.collect_metrics()
            monitor.metrics_history.append(metrics)
            time.sleep(1)
        
        monitor.export_metrics(args.export)
        print(f"Metrics exported to {args.export}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
