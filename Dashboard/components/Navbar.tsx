import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Home, Settings as SettingsIcon, Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";

const Navbar = () => {
  const { theme, setTheme } = useTheme();

  return (
    <nav className="flex items-center justify-between mb-8">
      <div className="flex items-center space-x-1">
        <Link to="/">
          <Button variant="ghost" size="sm" className="flex items-center">
            <Home className="mr-2 h-4 w-4" />
            Dashboard
          </Button>
        </Link>
      </div>
      <div className="flex items-center space-x-2">
        <Button 
          variant="outline" 
          size="icon" 
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="mr-2"
        >
          {theme === "dark" ? <Sun className="h-[1.2rem] w-[1.2rem]" /> : <Moon className="h-[1.2rem] w-[1.2rem]" />}
        </Button>
        <Link to="/settings">
          <Button variant="outline" size="sm" className="flex items-center">
            <SettingsIcon className="mr-2 h-4 w-4" />
            Settings
          </Button>
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;