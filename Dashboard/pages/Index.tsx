import NetworkStatusOverview from "@/components/NetworkStatusOverview";
import AttackHistory from "@/components/AttackHistory";
import ActiveAttacks from "@/components/ActiveAttacks";
import Navbar from "@/components/Navbar";
import { useToast } from "@/hooks/use-toast";
import { useEffect, useState } from "react";
import securityService from "@/services/securityService";
import { NetworkStatus } from "@/types/security";

const Index = () => {
  const { toast } = useToast();
  const [prevStatus, setPrevStatus] = useState<NetworkStatus | null>(null);
  
  useEffect(() => {
    const unsubscribe = securityService.subscribe((status) => {
      // Check if this is the first update or if we have a previous status
      if (prevStatus) {
        // Check if any new attacks have been detected
        if (status.lastAttack && (!prevStatus.lastAttack || 
            status.lastAttack.id !== prevStatus.lastAttack.id)) {
          // Show a toast notification for the new attack
          toast({
            title: `${status.lastAttack.type === 'deauth' ? 'Deauthentication Attack' : 
                    status.lastAttack.type === 'wifi_jamming' ? 'WiFi Jamming' : 
                    status.lastAttack.type === 'bluetooth_jamming' ? 'Bluetooth Jamming' : 
                    'GPS Jamming'} Detected!`,
            description: status.lastAttack.description,
            variant: status.lastAttack.severity === 'danger' ? 'destructive' : 'default'
          });
        }
      }
      
      setPrevStatus(status);
    });
    
    return unsubscribe;
  }, [toast, prevStatus]);

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-8">
        <Navbar />
        
        <header className="mb-10">
          <h1 className="text-3xl font-bold mb-1">ESP32 Security Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor wireless security threats in real-time
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-6 gap-6">
          {/* Network Status Section */}
          <div className="md:col-span-3">
            <NetworkStatusOverview />
          </div>
          
          {/* Active Attacks Section */}
          <div className="md:col-span-3">
            <ActiveAttacks />
          </div>
          
          {/* Attack History Section */}
          <div className="md:col-span-6">
            <AttackHistory />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;