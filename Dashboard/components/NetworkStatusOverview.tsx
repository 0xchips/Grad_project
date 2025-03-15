import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { NetworkStatus } from "@/types/security";
import securityService from "@/services/securityService";
import StatusIndicator from "./StatusIndicator";
import SignalStrengthMeter from "./SignalStrengthMeter";
import { Radio, Wifi, Bluetooth, Navigation } from "lucide-react";

const NetworkStatusOverview = () => {
  const [status, setStatus] = useState<NetworkStatus | null>(null);

  useEffect(() => {
    const unsubscribe = securityService.subscribe(setStatus);
    return unsubscribe;
  }, []);

  if (!status) {
    return <div>Loading...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Network Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-3 mb-6">
          <StatusIndicator 
            status={status.wifiStatus} 
            label="WiFi Security"
            className="bg-secondary/30"
          />
          <StatusIndicator 
            status={status.bluetoothStatus} 
            label="Bluetooth Security"
            className="bg-secondary/30"
          />
          <StatusIndicator 
            status={status.rfStatus} 
            label="RF Spectrum"
            className="bg-secondary/30"
          />
          <StatusIndicator 
            status={status.gpsStatus} 
            label="GPS"
            className="bg-secondary/30"
          />
        </div>
        
        <div className="space-y-4">
          <SignalStrengthMeter 
            type="wifi" 
            strength={status.wifiSignalStrength} 
            status={status.wifiStatus}
          />
          <SignalStrengthMeter 
            type="bluetooth" 
            strength={status.bluetoothSignalStrength} 
            status={status.bluetoothStatus}
          />
          
          <div className="mt-4 grid grid-cols-4 gap-3">
            <div className="flex items-center justify-center p-3 bg-secondary/30 rounded-lg">
              <Wifi className="w-6 h-6 text-security-info mr-2" />
              <div className="text-sm font-medium">
                {status.wifiStatus === 'safe' ? 'Protected' : 'At Risk'}
              </div>
            </div>
            <div className="flex items-center justify-center p-3 bg-secondary/30 rounded-lg">
              <Bluetooth className="w-6 h-6 text-security-info mr-2" />
              <div className="text-sm font-medium">
                {status.bluetoothStatus === 'safe' ? 'Protected' : 'At Risk'}
              </div>
            </div>
            <div className="flex items-center justify-center p-3 bg-secondary/30 rounded-lg">
              <Radio className="w-6 h-6 text-security-info mr-2" />
              <div className="text-sm font-medium">
                {status.rfStatus === 'safe' ? 'No Jamming' : 'Jamming Detected'}
              </div>
            </div>
            <div className="flex items-center justify-center p-3 bg-secondary/30 rounded-lg">
              <Navigation className="w-6 h-6 text-security-info mr-2" />
              <div className="text-sm font-medium">
                {status.gpsStatus === 'safe' ? 'GPS Normal' : 'GPS Jammed'}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default NetworkStatusOverview;