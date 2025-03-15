import { AttackEvent } from "@/types/security";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import securityService from "@/services/securityService";

interface AttackAlertProps {
  attack: AttackEvent;
  className?: string;
}

const AttackAlert = ({ attack, className }: AttackAlertProps) => {
  const handleAcknowledge = () => {
    securityService.acknowledgeAttack(attack.id);
  };

  const getTypeIcon = () => {
    return <AlertTriangle className="w-5 h-5 mr-2" />;
  };

  const getSeverityClass = () => {
    switch (attack.severity) {
      case 'warning':
        return 'border-security-warning bg-security-warning/20';
      case 'danger':
        return 'border-security-danger bg-security-danger/20';
      default:
        return 'border-security-info bg-security-info/20';
    }
  };

  const getTypeLabel = () => {
    switch (attack.type) {
      case 'deauth':
        return 'Deauthentication Attack';
      case 'wifi_jamming':
        return 'WiFi Jamming';
      case 'bluetooth_jamming':
        return 'Bluetooth Jamming';
      case 'gps_jamming':
        return 'GPS Jamming';
      default:
        return 'Unknown Attack';
    }
  };

  return (
    <Card className={cn(
      "mb-4 p-4 border-l-4 shadow-sm",
      getSeverityClass(),
      className
    )}>
      <div className="flex justify-between">
        <div className="flex items-center font-bold">
          {getTypeIcon()}
          {getTypeLabel()}
          {attack.severity === 'danger' && (
            <span className="bg-security-danger text-white text-xs font-semibold ml-2 px-2 py-0.5 rounded">
              CRITICAL
            </span>
          )}
        </div>
        <Button variant="ghost" size="icon" onClick={handleAcknowledge}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      
      <p className="text-sm my-2">{attack.description}</p>
      
      <div className="flex justify-between text-xs text-muted-foreground mt-2">
        <div>
          {attack.source && <span>Source: {attack.source}</span>}
          {attack.targetNetwork && <span className="ml-4">Target: {attack.targetNetwork}</span>}
        </div>
        <div>
          {formatDistanceToNow(new Date(attack.timestamp), { addSuffix: true })}
        </div>
      </div>
    </Card>
  );
};

export default AttackAlert;