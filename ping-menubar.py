from collections import deque
from time import time
from typing import Optional
import re
import subprocess

from AppKit import (
    NSApplication,
    NSBezierPath,
    NSColor,
    NSCompositingOperationSourceOver,
    NSImage,
    NSMakeRect,
    NSMenu,
    NSMenuItem,
    NSPoint,
    NSStatusBar,
    NSVariableStatusItemLength,
)
from Foundation import (
    NSObject,
    NSRunLoop,
    NSTimer,
)
from ServiceManagement import (
    SMAppService,   
    SMAppServiceStatusEnabled,
)

# Configuration
PING_HOST = "1.1.1.1"
PING_INTERVAL = 2.0  # seconds
PING_SAMPLES = 16    # number of readings to show
PING_WAIT = 1000     # ping -W value in ms

# Ping time ranges and colors (RGB)
TIERS = [
    {"limit": 0, "color": NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 1.0)},
    {"limit": 70, "color": NSColor.colorWithRed_green_blue_alpha_(13/255, 215/255, 33/255, 1.0)},
    {"limit": 150, "color": NSColor.colorWithRed_green_blue_alpha_(209/255, 214/255, 39/255, 1.0)},
    {"limit": 300, "color": NSColor.colorWithRed_green_blue_alpha_(209/255, 15/255, 29/255, 1.0)},
]

BAR_WIDTH = 3
BAR_HEIGHT = 18

class PingMonitor(NSObject):
    def init(self):
        self.times = deque([0] * PING_SAMPLES, maxlen=PING_SAMPLES)
        self.width = PING_SAMPLES * BAR_WIDTH
        self.statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(self.width)
        
        # Add menu items
        self.menu = NSMenu.new()
        self.startup_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Launch at Login", "toggleStartup:", ""
        )
        self.startup_item.setTarget_(self)
        self.menu.addItem_(self.startup_item)

        self.quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", "q"
        )
        self.menu.addItem_(NSMenuItem.separatorItem())
        self.menu.addItem_(self.quit_item)  
        self.statusitem.setMenu_(self.menu)
        
        # Add image
        self.image = NSImage.alloc().initWithSize_((self.width, BAR_HEIGHT))
        self.statusitem.setImage_(self.image)

        # ServiceManagement app instance, for Login Items
        self.service = SMAppService.mainAppService()
        self.updateStartupItemState()
    
        # Schedule update to run immediately.
        self.schedule_next_update(PING_INTERVAL)
        return self

    def schedule_next_update(self, processing_time):
        """Schedule next update cycle"""
        interval = max(0.1, PING_INTERVAL - processing_time)
        self.timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
            interval, self, 'update:', None, False
        )
        runLoop = NSRunLoop.currentRunLoop()
        runLoop.addTimer_forMode_(self.timer, "NSEventTrackingRunLoopMode")
        runLoop.addTimer_forMode_(self.timer, "NSDefaultRunLoopMode")

    def update_(self, timer):
        """Called every update cycle"""
        start = time()
        ping_time = self.get_ping_time()
        self.times.append(-1 if ping_time is None else ping_time)
        self.update_graph()
        self.schedule_next_update(time() - start)

    def get_ping_time(self) -> Optional[float]:
        """Subprocess call to ping"""
        try:
            result = subprocess.run(
                ['ping', '-W', str(PING_WAIT), '-c', '1', PING_HOST],
                capture_output=True,
                text=True,
                timeout=PING_INTERVAL,
            )
            if result.returncode == 0:
                if match := re.search(r'time=(\d+\.?\d*)\s*ms', result.stdout):
                    return float(match.group(1))
        except:
            pass    
        return None

    def update_graph(self):
        self.image.lockFocus()
        
        # Shift image left
        source_rect = NSMakeRect(BAR_WIDTH, 0, self.width - BAR_WIDTH, BAR_HEIGHT)
        self.image.compositeToPoint_fromRect_operation_(
            NSPoint(0, 0),
            source_rect,
            NSCompositingOperationSourceOver
        )
        
        # Draw new bar at rightmost position
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(NSMakeRect(self.width - BAR_WIDTH, 0, BAR_WIDTH, BAR_HEIGHT))
        self.draw_bar(self.times[-1], self.width - BAR_WIDTH)
        
        self.image.unlockFocus()
        self.statusitem.button().setNeedsDisplay_(True)

    def draw_bar(self, value: float, x: int):
        if value != -1:
            self.draw_time_bar(value, x)
        else:
            self.draw_error_bar(x)
        
    def draw_time_bar(self, value: float, x: int):
        # Select tier and draw
        prev_tier = TIERS[0]
        curr_tier = TIERS[1]
        for tier in TIERS[1:]:
            if value < tier["limit"]:
                curr_tier = tier
                break
            prev_tier = tier

        bar_range = curr_tier["limit"] - prev_tier["limit"]
        bar_height = int((value - prev_tier["limit"]) / bar_range * BAR_HEIGHT)
        
        # Current tier bar
        curr_tier["color"].set()
        NSBezierPath.fillRect_(NSMakeRect(x, 0, BAR_WIDTH, bar_height))
        
        # Background tier bar
        prev_tier["color"].set()
        NSBezierPath.fillRect_(NSMakeRect(x, bar_height, BAR_WIDTH, BAR_HEIGHT - bar_height))

    def draw_error_bar(self, x: int):
        background_color = TIERS[0]["color"]
        background_color.set()
        NSBezierPath.fillRect_(NSMakeRect(x, 0, BAR_WIDTH, BAR_HEIGHT))
        
        error_color = TIERS[-1]["color"]
        error_color.set()
        lower_bar_height = int(BAR_HEIGHT * 0.63)
        gap_end = int(BAR_HEIGHT * 0.85)
        NSBezierPath.fillRect_(NSMakeRect(x + 1, BAR_HEIGHT - lower_bar_height, 1, lower_bar_height))
        NSBezierPath.fillRect_(NSMakeRect(x + 1, 0, 1, BAR_HEIGHT - gap_end))
        return

    def updateStartupItemState(self):
        """Update the menu item's state based on whether the app is registered as a login item"""
        is_registered = self.service.status() == SMAppServiceStatusEnabled
        self.startup_item.setState_(1 if is_registered else 0)
    
    def toggleStartup_(self, sender):
        """Toggle login item registration"""
        try:
            if self.service.status() == SMAppServiceStatusEnabled:
                self.service.unregisterAndReturnError_(None)
            else:
                self.service.registerAndReturnError_(None)
            self.updateStartupItemState()
        except Exception as e:
            print(f"Error toggling startup status: {e}")

def main():
    app = NSApplication.sharedApplication()
    monitor = PingMonitor.alloc().init()
    app.run()

if __name__ == "__main__":
    main()