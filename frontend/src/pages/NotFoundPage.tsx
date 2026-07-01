import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Home } from "lucide-react";
import { Button } from "../components/ui/Button";

export default function NotFoundPage() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "var(--bg-base)", color: "var(--text-primary)", textAlign: "center", padding: "2rem" }}>
      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div style={{ fontSize: "6rem", fontWeight: 800, fontFamily: "var(--font-heading)", background: "var(--gradient-primary)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", lineHeight: 1 }}>404</div>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.5rem", margin: "1rem 0 0.5rem" }}>Page not found</h1>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>The page you're looking for doesn't exist.</p>
        <Link to="/dashboard"><Button variant="primary" leftIcon={<Home size={16} />}>Back to Dashboard</Button></Link>
      </motion.div>
    </div>
  );
}
