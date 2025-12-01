"""
Disk space monitoring utility for all runners
"""
import os
import shutil
import sqlite3
from typing import Tuple, Optional

class DiskSpaceMonitor:
    """Monitor disk space and database size with emergency shutdown"""
    
    # Thresholds (in GB)
    MIN_FREE_SPACE_GB = 15.0  # Minimum free space on drive
    MAX_DB_SIZE_GB = 10.0     # Maximum database size
    CRITICAL_FREE_SPACE_GB = 5.0  # Emergency stop threshold
    
    def __init__(self, db_path: str = 'core_data.db'):
        self.db_path = db_path
        self.drive = os.path.splitdrive(os.path.abspath(db_path))[0]
        
    def check_disk_space(self) -> Tuple[bool, str, dict]:
        """
        Check disk space and database size
        
        Returns:
            (safe_to_continue, warning_message, stats_dict)
        """
        stats = {}
        
        # Get drive free space
        drive_stats = shutil.disk_usage(self.drive)
        free_gb = drive_stats.free / (1024**3)
        total_gb = drive_stats.total / (1024**3)
        used_gb = drive_stats.used / (1024**3)
        
        stats['drive_free_gb'] = free_gb
        stats['drive_total_gb'] = total_gb
        stats['drive_used_gb'] = used_gb
        stats['drive_free_pct'] = (free_gb / total_gb) * 100
        
        # Get database size
        if os.path.exists(self.db_path):
            db_size_gb = os.path.getsize(self.db_path) / (1024**3)
            stats['db_size_gb'] = db_size_gb
        else:
            db_size_gb = 0
            stats['db_size_gb'] = 0
            
        # Check thresholds
        warnings = []
        critical = False
        
        # Critical: Disk almost full
        if free_gb < self.CRITICAL_FREE_SPACE_GB:
            critical = True
            warnings.append(f"🚨 CRITICAL: Only {free_gb:.2f} GB free (< {self.CRITICAL_FREE_SPACE_GB} GB)")
            
        # Warning: Low disk space
        elif free_gb < self.MIN_FREE_SPACE_GB:
            warnings.append(f"⚠️ WARNING: Low disk space - {free_gb:.2f} GB free (< {self.MIN_FREE_SPACE_GB} GB)")
            
        # Warning: Database too large
        if db_size_gb > self.MAX_DB_SIZE_GB:
            msg = f"⚠️ WARNING: Database is {db_size_gb:.2f} GB (> {self.MAX_DB_SIZE_GB} GB limit)"
            warnings.append(msg)
            if db_size_gb > self.MAX_DB_SIZE_GB * 2:
                critical = True
                warnings.append(f"🚨 CRITICAL: Database is {(db_size_gb/self.MAX_DB_SIZE_GB):.1f}x over limit!")
                
        # Build message
        if warnings:
            message = "\n".join(warnings)
            message += f"\n\nStats: {free_gb:.2f} GB free / {total_gb:.2f} GB total"
            message += f"\nDatabase: {db_size_gb:.2f} GB"
        else:
            message = f"✓ Disk space OK: {free_gb:.2f} GB free, DB: {db_size_gb:.2f} GB"
            
        safe_to_continue = not critical
        
        return safe_to_continue, message, stats
    
    def get_table_sizes(self, top_n: int = 10) -> list:
        """Get sizes of largest tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        table_sizes = []
        for (table_name,) in tables:
            try:
                count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                table_sizes.append((table_name, count))
            except:
                pass
                
        conn.close()
        
        # Sort by count descending
        table_sizes.sort(key=lambda x: x[1], reverse=True)
        return table_sizes[:top_n]
    
    def suggest_cleanup_actions(self) -> list:
        """Suggest specific cleanup actions based on table sizes"""
        suggestions = []
        
        table_sizes = self.get_table_sizes(20)
        
        for table, count in table_sizes:
            if table == 'action_traces' and count > 1_000_000:
                suggestions.append(f"• Delete old action_traces (currently {count:,} rows)")
            elif table == 'game_results' and count > 100_000:
                suggestions.append(f"• Archive old game_results (currently {count:,} rows)")
            elif table == 'viral_packages' and count > 50_000:
                suggestions.append(f"• Prune low-value viral_packages (currently {count:,} rows)")
            elif table == 'pariah_patterns' and count > 50_000:
                suggestions.append(f"• Clean old pariah_patterns (currently {count:,} rows)")
                
        return suggestions


def check_disk_space_or_abort(logger=None) -> bool:
    """
    Convenience function: Check disk space and abort if critical
    
    Returns:
        True if safe to continue, False if should abort
    """
    monitor = DiskSpaceMonitor()
    safe, message, stats = monitor.check_disk_space()
    
    if logger:
        if safe:
            logger.info(message)
        else:
            logger.critical(message)
            logger.critical("ABORTING: Disk space critical!")
            
            # Show cleanup suggestions
            suggestions = monitor.suggest_cleanup_actions()
            if suggestions:
                logger.warning("Cleanup suggestions:")
                for s in suggestions:
                    logger.warning(f"  {s}")
    else:
        print(message)
        if not safe:
            print("\n🚨 ABORTING: Disk space critical!")
            suggestions = monitor.suggest_cleanup_actions()
            if suggestions:
                print("\nCleanup suggestions:")
                for s in suggestions:
                    print(f"  {s}")
    
    return safe


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DISK SPACE MONITORING REPORT")
    print("=" * 80)
    
    monitor = DiskSpaceMonitor()
    safe, message, stats = monitor.check_disk_space()
    
    print(f"\n{message}")
    
    print("\n" + "-" * 80)
    print("LARGEST TABLES:")
    print("-" * 80)
    
    table_sizes = monitor.get_table_sizes(15)
    for table, count in table_sizes:
        print(f"  {table:30s}: {count:>12,} rows")
        
    if not safe:
        print("\n" + "=" * 80)
        print("CLEANUP SUGGESTIONS:")
        print("=" * 80)
        suggestions = monitor.suggest_cleanup_actions()
        for s in suggestions:
            print(f"  {s}")
