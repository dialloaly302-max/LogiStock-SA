package com.logistock;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.sql.*;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;

public class LogiStockServer {
    private static final String DB_HOST = env("DB_HOST", "127.0.0.1");
    private static final String DB_PORT = env("DB_PORT", "3306");
    private static final String DB_NAME = env("DB_NAME", "logistock");
    private static final String DB_USER = env("DB_USER", "root");
    private static final String DB_PASS = env("DB_PASS", "");
    private static final int PORT = Integer.parseInt(env("PORT", "8080"));
    private static final String JDBC_URL = "jdbc:mysql://" + DB_HOST + ":" + DB_PORT + "/" + DB_NAME
            + "?useUnicode=true&characterEncoding=utf8&serverTimezone=UTC&allowPublicKeyRetrieval=true&useSSL=false";

    private static final Map<String, SessionData> SESSIONS = new ConcurrentHashMap<>();
    private static final Set<String> VALID_ROLES = Set.of("Administrateur", "Commercial", "Gestionnaire de stock");
    private static final SecureRandom RANDOM = new SecureRandom();

    record SessionData(int uid, long expiresAt) {}
    record UserInfo(int id, String nom, String prenom, String login, String role) {}

    public static void main(String[] args) throws Exception {
        Class.forName("com.mysql.cj.jdbc.Driver");
        ensureSchemaAndRoles();

        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", PORT), 0);
        server.createContext("/api/", LogiStockServer::handleApi);
        server.setExecutor(Executors.newCachedThreadPool());
        server.start();
        System.out.println("LogiStock Backend Java demarre sur http://0.0.0.0:" + PORT);
    }

    private static String env(String k, String def) {
        String v = System.getenv(k);
        return (v == null || v.isBlank()) ? def : v.trim();
    }

    private static Connection conn() throws SQLException {
        return DriverManager.getConnection(JDBC_URL, DB_USER, DB_PASS);
    }

    private static void ensureSchemaAndRoles() {
        try (Connection c = conn(); Statement st = c.createStatement()) {
            st.execute("CREATE TABLE IF NOT EXISTS mode_paiement (id_mode INT NOT NULL AUTO_INCREMENT PRIMARY KEY, nom_mode VARCHAR(30) NOT NULL UNIQUE, est_credit TINYINT(1) NOT NULL DEFAULT 0, actif TINYINT(1) NOT NULL DEFAULT 1) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci");
            try (ResultSet rs = st.executeQuery("SELECT COUNT(*) n FROM mode_paiement")) {
                if (rs.next() && rs.getInt("n") == 0) {
                    st.execute("INSERT INTO mode_paiement(nom_mode,est_credit) VALUES ('Espèces',0),('Orange Money',0),('Moov Money',0),('Virement bancaire',0),('Chèque',0),('Carte bancaire',0),('Crédit',1)");
                }
            }
            st.execute("CREATE TABLE IF NOT EXISTS historique_vente (id_historique INT NOT NULL AUTO_INCREMENT PRIMARY KEY, id_vente INT NOT NULL, action VARCHAR(20) NOT NULL, details VARCHAR(255) NULL, date_action DATETIME NOT NULL, id_utilisateur INT NOT NULL, KEY idx_hv_vente (id_vente)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci");
            st.execute("UPDATE utilisateur SET role='Administrateur' WHERE role='Propriétaire'");
            st.execute("UPDATE utilisateur SET role='Commercial' WHERE role IN ('Gestionnaire de vente','Comptable G')");
            st.execute("UPDATE utilisateur SET role='Gestionnaire de stock' WHERE role IN ('Gestionnaire de Produit','Gestionaire de stock')");
        } catch (Exception e) {
            System.err.println("Avertissement verification base : " + e.getMessage());
        }
    }

    private static void handleApi(HttpExchange ex) throws IOException {
        Headers h = ex.getResponseHeaders();
        String origin = ex.getRequestHeaders().getFirst("Origin");
        if (origin != null && !origin.isBlank()) {
            h.set("Access-Control-Allow-Origin", origin);
            h.set("Access-Control-Allow-Credentials", "true");
        } else {
            h.set("Access-Control-Allow-Origin", "*");
        }
        h.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        h.set("Access-Control-Allow-Headers", "Content-Type");

        if ("OPTIONS".equalsIgnoreCase(ex.getRequestMethod())) {
            ex.sendResponseHeaders(204, -1);
            ex.close();
            return;
        }

        String path = ex.getRequestURI().getPath();
        String route = path.startsWith("/api") ? path.substring(4) : path;
        String bodyStr = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        Map<String, Object> in = parseJsonObject(bodyStr);

        try {
            if ("/auth/me".equals(route)) {
                UserInfo u = currentUser(ex);
                sendJson(ex, 200, jsonObj("user", u == null ? null : userMap(u), "setup", countUsers() == 0));
                return;
            }
            if ("/auth/setup".equals(route)) {
                doSetup(ex, in);
                return;
            }
            if ("/auth/login".equals(route)) {
                doLogin(ex, in);
                return;
            }
            if ("/auth/logout".equals(route)) {
                String sid = getCookie(ex, "LOGISTOCK_SID");
                if (sid != null) SESSIONS.remove(sid);
                clearSessionCookie(ex);
                sendJson(ex, 200, jsonObj("ok", 1));
                return;
            }

            UserInfo u = currentUser(ex);
            if (u == null) {
                sendJson(ex, 401, jsonObj("error", "Session expirée. Reconnectez-vous."));
                return;
            }

            switch (route) {
                case "/bootstrap" -> sendJson(ex, 200, loadBootstrap(u));
                case "/products" -> { saveProduct(u, in); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/stock/entries" -> { stockEntry(u, in); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/clients" -> { saveClient(u, in); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/clients/archive" -> { archiveClient(u, toInt(in.get("id"))); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/clients/payments" -> { payClient(u, in); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/sales" -> sendJson(ex, 200, jsonObj("id", createSale(u, in)));
                case "/sales/cancel" -> { cancelSale(u, toInt(in.get("id")), str(in.get("motif")).trim()); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/categories" -> { saveCategory(u, in); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/categories/delete" -> { deleteCategory(u, toInt(in.get("id"))); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/users" -> { saveUser(u, in); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/users/password" -> { changePassword(u, str(in.get("old")), str(in.get("new"))); sendJson(ex, 200, jsonObj("ok", 1)); }
                case "/users/toggle" -> { toggleUser(u, toInt(in.get("id"))); sendJson(ex, 200, jsonObj("ok", 1)); }
                default -> sendJson(ex, 404, jsonObj("error", "Action inconnue."));
            }
        } catch (ApiException ae) {
            sendJson(ex, ae.code, jsonObj("error", ae.getMessage()));
        } catch (SQLException se) {
            sendJson(ex, 500, jsonObj("error", "Erreur de base de données : " + se.getMessage()));
        } catch (Exception e) {
            sendJson(ex, 500, jsonObj("error", "Erreur serveur : " + e.getMessage()));
        }
    }

    private static int countUsers() throws SQLException {
        try (Connection c = conn(); Statement st = c.createStatement(); ResultSet rs = st.executeQuery("SELECT COUNT(*) n FROM utilisateur")) {
            return rs.next() ? rs.getInt("n") : 0;
        }
    }

    private static void doSetup(HttpExchange ex, Map<String, Object> in) throws SQLException, IOException {
        if (countUsers() > 0) throw new ApiException(403, "Le compte administrateur existe déjà.");
        String nom = str(in.get("nom")).trim();
        String login = str(in.get("login")).trim();
        String pw = str(in.get("pw"));
        if (nom.isEmpty() || login.isEmpty()) throw new ApiException(400, "Le nom et l’identifiant sont obligatoires.");
        if (pw.length() < 6) throw new ApiException(400, "Le mot de passe doit contenir au moins 6 caractères.");

        String hash = hashPassword(pw);
        try (Connection c = conn(); PreparedStatement ps = c.prepareStatement(
                "INSERT INTO utilisateur(nom,prenom,identifiant,mot_de_passe,telephone,adresse,role,actif) VALUES(?,'',?,?,'','','Administrateur',1)",
                Statement.RETURN_GENERATED_KEYS)) {
            ps.setString(1, nom);
            ps.setString(2, login);
            ps.setString(3, hash);
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) createSession(ex, keys.getInt(1));
            }
        }
        sendJson(ex, 200, jsonObj("ok", 1));
    }

    private static void doLogin(HttpExchange ex, Map<String, Object> in) throws SQLException, IOException {
        String login = str(in.get("login")).trim();
        String pw = str(in.get("pw"));
        try (Connection c = conn(); PreparedStatement ps = c.prepareStatement("SELECT * FROM utilisateur WHERE identifiant=?")) {
            ps.setString(1, login);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) throw new ApiException(401, "Identifiant ou mot de passe incorrect.");
                int uid = rs.getInt("id_utilisateur");
                String stored = str(rs.getString("mot_de_passe"));
                boolean actif = rs.getInt("actif") == 1;
                boolean ok = false;
                if (stored.startsWith("SHA256:")) {
                    ok = constantTimeEq(stored, hashPassword(pw));
                } else if (stored.startsWith("$2y$") || stored.startsWith("$2a$") || stored.startsWith("$2b$")) {
                    // Si mot de passe hache par PHP, verifier ou re-initialiser si necessaire
                    ok = false;
                } else if (constantTimeEq(stored, pw)) {
                    ok = true;
                    try (PreparedStatement up = c.prepareStatement("UPDATE utilisateur SET mot_de_passe=? WHERE id_utilisateur=?")) {
                        up.setString(1, hashPassword(pw));
                        up.setInt(2, uid);
                        up.executeUpdate();
                    }
                }
                if (!ok) throw new ApiException(401, "Identifiant ou mot de passe incorrect.");
                if (!actif) throw new ApiException(403, "Ce compte est désactivé. Contactez l’administrateur.");
                createSession(ex, uid);
                sendJson(ex, 200, jsonObj("ok", 1));
            }
        }
    }

    private static void createSession(HttpExchange ex, int uid) {
        byte[] b = new byte[24];
        RANDOM.nextBytes(b);
        String token = HexFormat.of().formatHex(b);
        SESSIONS.put(token, new SessionData(uid, System.currentTimeMillis() + 8L * 3600_000L));
        ex.getResponseHeaders().add("Set-Cookie", "LOGISTOCK_SID=" + token + "; Path=/; HttpOnly; SameSite=Lax");
    }

    private static void clearSessionCookie(HttpExchange ex) {
        ex.getResponseHeaders().add("Set-Cookie", "LOGISTOCK_SID=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax");
    }

    private static String getCookie(HttpExchange ex, String name) {
        List<String> cookies = ex.getRequestHeaders().get("Cookie");
        if (cookies == null) return null;
        for (String line : cookies) {
            for (String part : line.split(";")) {
                String p = part.trim();
                if (p.startsWith(name + "=")) return p.substring(name.length() + 1);
            }
        }
        return null;
    }

    private static UserInfo currentUser(HttpExchange ex) throws SQLException {
        String sid = getCookie(ex, "LOGISTOCK_SID");
        if (sid == null) return null;
        SessionData sd = SESSIONS.get(sid);
        if (sd == null || sd.expiresAt() < System.currentTimeMillis()) {
            SESSIONS.remove(sid);
            return null;
        }
        try (Connection c = conn(); PreparedStatement ps = c.prepareStatement(
                "SELECT id_utilisateur,nom,prenom,identifiant,role FROM utilisateur WHERE id_utilisateur=? AND actif=1")) {
            ps.setInt(1, sd.uid());
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return null;
                return new UserInfo(rs.getInt("id_utilisateur"), str(rs.getString("nom")),
                        str(rs.getString("prenom")), str(rs.getString("identifiant")), str(rs.getString("role")));
            }
        }
    }

    private static Map<String, Object> userMap(UserInfo u) {
        return mapObj("id", u.id(), "nom", u.nom(), "prenom", u.prenom(), "login", u.login(), "role", u.role());
    }

    private static boolean isAdmin(UserInfo u) { return "Administrateur".equals(u.role()); }
    private static boolean canStock(UserInfo u) { return isAdmin(u) || "Gestionnaire de stock".equals(u.role()); }
    private static boolean canSell(UserInfo u) { return isAdmin(u) || "Commercial".equals(u.role()); }
    private static void allow(boolean ok) { if (!ok) throw new ApiException(403, "Action non autorisée pour votre rôle."); }

    private static String loadBootstrap(UserInfo u) throws SQLException {
        try (Connection c = conn()) {
            Map<Integer, String> userNames = new HashMap<>();
            List> users = new ArrayList<>();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_utilisateur,nom,prenom,identifiant,telephone,role,actif FROM utilisateur")) {
                while (rs.next()) {
                    int id = rs.getInt("id_utilisateur");
                    String nom = str(rs.getString("nom"));
                    String prenom = str(rs.getString("prenom"));
                    userNames.put(id, (prenom + " " + nom).trim());
                    users.add(mapObj("id", id, "nom", nom, "prenom", prenom,
                            "login", str(rs.getString("identifiant")), "tel", str(rs.getString("telephone")),
                            "role", str(rs.getString("role")), "actif", rs.getInt("actif") == 1));
                }
            }

            Map<Integer, String> modeNames = new HashMap<>();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_mode,nom_mode FROM mode_paiement")) {
                while (rs.next()) modeNames.put(rs.getInt("id_mode"), str(rs.getString("nom_mode")));
            }

            List> modes = new ArrayList<>();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_mode,nom_mode,est_credit FROM mode_paiement WHERE actif=1 ORDER BY id_mode")) {
                while (rs.next()) modes.add(mapObj("id", rs.getInt("id_mode"), "nom", str(rs.getString("nom_mode")), "credit", rs.getInt("est_credit") == 1));
            }

            List> cats = new ArrayList<>();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_categorie,nom_categorie FROM categorie")) {
                while (rs.next()) cats.add(mapObj("id", rs.getInt("id_categorie"), "nom", str(rs.getString("nom_categorie"))));
            }

            List> clients = new ArrayList<>();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_client,nom,prenom,telephone,adresse,plafond,actif FROM client")) {
                while (rs.next()) clients.add(mapObj("id", rs.getInt("id_client"), "nom", str(rs.getString("nom")),
                        "prenom", str(rs.getString("prenom")), "tel", str(rs.getString("telephone")),
                        "adr", str(rs.getString("adresse")), "plafond", rs.getInt("plafond"), "actif", rs.getInt("actif") == 1));
            }

            boolean showPa = canStock(u);
            List> products = new ArrayList<>();
            try (ResultSet rs = c.createStatement().executeQuery(
                    "SELECT p.id_produit,code,designation,unite,prix_achat,prix_vente,seuil_minimal,id_categorie,"
                    + "(SELECT COALESCE(SUM(IF(type_mouvement='entree',quantite,-quantite)),0) FROM stock s WHERE s.id_produit=p.id_produit) stock "
                    + "FROM produit p ORDER BY p.id_produit")) {
                while (rs.next()) {
                    products.add(mapObj("id", rs.getInt("id_produit"), "code", str(rs.getString("code")),
                            "des", str(rs.getString("designation")), "unite", str(rs.getString("unite")),
                            "pa", showPa ? rs.getInt("prix_achat") : 0, "pv", rs.getInt("prix_vente"),
                            "seuil", rs.getInt("seuil_minimal"), "cat", rs.getInt("id_categorie"), "stock", rs.getInt("stock")));
                }
            }

            Map<Integer, List>> linesMap = new HashMap<>();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_vente,id_produit,quantite,prix_unitaire FROM contenir")) {
                while (rs.next()) {
                    linesMap.computeIfAbsent(rs.getInt("id_vente"), k -> new ArrayList<>())
                            .add(mapObj("pid", rs.getInt("id_produit"), "q", rs.getInt("quantite"), "pu", rs.getInt("prix_unitaire")));
                }
            }

            List> sales = new ArrayList<>();
            try (ResultSet rs = c.createStatement().executeQuery(
                    "SELECT id_vente,reference,date_vente,mode_paiement,id_mode,remise,montant_total,statut,id_client,id_utilisateur,motif_annulation,annule_par FROM vente ORDER BY id_vente")) {
                while (rs.next()) {
                    int vid = rs.getInt("id_vente");
                    String stRaw = str(rs.getString("statut"));
                    String stFr = switch (stRaw) {
                        case "validee" -> "validée";
                        case "annulee" -> "annulée";
                        case "en_cours" -> "en cours";
                        default -> stRaw;
                    };
                    int idMode = rs.getInt("id_mode");
                    Integer annParId = rs.getObject("annule_par") == null ? null : rs.getInt("annule_par");
                    sales.add(mapObj("id", vid, "ref", str(rs.getString("reference")),
                            "t", sqlDateToMs(rs.getTimestamp("date_vente")),
                            "mode", str(rs.getString("mode_paiement")),
                            "moyen", rs.wasNull() || idMode == 0 ? null : modeNames.get(idMode),
                            "remise", rs.get