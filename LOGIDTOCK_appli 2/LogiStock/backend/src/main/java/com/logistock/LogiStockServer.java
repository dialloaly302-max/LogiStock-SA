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
        Map in = parseJsonObject(bodyStr);

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

    private static void doSetup(HttpExchange ex, Map in) throws SQLException, IOException {
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

    private static void doLogin(HttpExchange ex, Map in) throws SQLException, IOException {
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
        List cookies = ex.getRequestHeaders().get("Cookie");
        if (cookies == null) return null;
        for (Object item : cookies) {
            String line = String.valueOf(item);
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

    private static Map userMap(UserInfo u) {
        return mapObj("id", u.id(), "nom", u.nom(), "prenom", u.prenom(), "login", u.login(), "role", u.role());
    }

    private static boolean isAdmin(UserInfo u) { return "Administrateur".equals(u.role()); }
    private static boolean canStock(UserInfo u) { return isAdmin(u) || "Gestionnaire de stock".equals(u.role()); }
    private static boolean canSell(UserInfo u) { return isAdmin(u) || "Commercial".equals(u.role()); }
    private static void allow(boolean ok) { if (!ok) throw new ApiException(403, "Action non autorisée pour votre rôle."); }

    private static String loadBootstrap(UserInfo u) throws SQLException {
        try (Connection c = conn()) {
            Map<Integer, String> userNames = new HashMap<>();
            List users = new ArrayList();
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

            List modes = new ArrayList();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_mode,nom_mode,est_credit FROM mode_paiement WHERE actif=1 ORDER BY id_mode")) {
                while (rs.next()) modes.add(mapObj("id", rs.getInt("id_mode"), "nom", str(rs.getString("nom_mode")), "credit", rs.getInt("est_credit") == 1));
            }

            List cats = new ArrayList();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_categorie,nom_categorie FROM categorie")) {
                while (rs.next()) cats.add(mapObj("id", rs.getInt("id_categorie"), "nom", str(rs.getString("nom_categorie"))));
            }

            List clients = new ArrayList();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_client,nom,prenom,telephone,adresse,plafond,actif FROM client")) {
                while (rs.next()) clients.add(mapObj("id", rs.getInt("id_client"), "nom", str(rs.getString("nom")),
                        "prenom", str(rs.getString("prenom")), "tel", str(rs.getString("telephone")),
                        "adr", str(rs.getString("adresse")), "plafond", rs.getInt("plafond"), "actif", rs.getInt("actif") == 1));
            }

            boolean showPa = canStock(u);
            List products = new ArrayList();
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

            Map<Integer, List> linesMap = new HashMap<>();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_vente,id_produit,quantite,prix_unitaire FROM contenir")) {
                while (rs.next()) {
                    int vid = rs.getInt("id_vente");
                    List l = (List) linesMap.get(vid);
                    if (l == null) {
                        l = new ArrayList();
                        linesMap.put(vid, l);
                    }
                    l.add(mapObj("pid", rs.getInt("id_produit"), "q", rs.getInt("quantite"), "pu", rs.getInt("prix_unitaire")));
                }
            }

            List sales = new ArrayList();
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
                    Object lignesObj = linesMap.get(vid);
                    sales.add(mapObj("id", vid, "ref", str(rs.getString("reference")),
                            "t", sqlDateToMs(rs.getTimestamp("date_vente")),
                            "mode", str(rs.getString("mode_paiement")),
                            "moyen", rs.wasNull() || idMode == 0 ? null : modeNames.get(idMode),
                            "remise", rs.getInt("remise"), "total", rs.getInt("montant_total"),
                            "statut", stFr, "cid", rs.getInt("id_client"), "uid", rs.getInt("id_utilisateur"),
                            "motif", rs.getString("motif_annulation"),
                            "annPar", annParId == null ? null : userNames.get(annParId),
                            "lignes", lignesObj == null ? List.of() : lignesObj));
                }
            }

            List moves = new ArrayList();
            try (ResultSet rs = c.createStatement().executeQuery(
                    "SELECT id_stock,date_mouvement,type_mouvement,id_produit,quantite,quantite_restante,id_utilisateur,id_vente FROM stock ORDER BY date_mouvement DESC,id_stock DESC")) {
                while (rs.next()) {
                    Integer sid = rs.getObject("id_vente") == null ? null : rs.getInt("id_vente");
                    moves.add(mapObj("id", rs.getInt("id_stock"),
                            "t", sqlDateToMs(rs.getTimestamp("date_mouvement")),
                            "type", "entree".equals(str(rs.getString("type_mouvement"))) ? "entrée" : "sortie",
                            "pid", rs.getInt("id_produit"), "q", rs.getInt("quantite"),
                            "rest", rs.getInt("quantite_restante"), "uid", rs.getInt("id_utilisateur"), "sid", sid));
                }
            }

            List histo = new ArrayList();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_vente,action,details,date_action,id_utilisateur FROM historique_vente ORDER BY id_historique")) {
                while (rs.next()) {
                    histo.add(mapObj("sid", rs.getInt("id_vente"), "action", str(rs.getString("action")),
                            "details", rs.getString("details"), "t", sqlDateToMs(rs.getTimestamp("date_action")),
                            "uid", rs.getInt("id_utilisateur")));
                }
            }

            List pays = new ArrayList();
            try (ResultSet rs = c.createStatement().executeQuery("SELECT id_client,date_paiement,montant FROM paiement")) {
                while (rs.next()) {
                    pays.add(mapObj("cid", rs.getInt("id_client"), "t", sqlDateToMs(rs.getTimestamp("date_paiement")), "m", rs.getInt("montant")));
                }
            }

            return jsonObj("cats", cats, "users", users, "clients", clients, "products", products,
                    "moves", moves, "sales", sales, "modes", modes, "histo", histo, "pays", pays);
        }
    }

    private static void saveProduct(UserInfo u, Map in) throws SQLException {
        allow(canStock(u));
        int id = toInt(in.get("id"));
        String code = str(in.get("code")).trim();
        String des = str(in.get("des")).trim();
        if (code.isEmpty() || des.isEmpty()) throw new ApiException(400, "Le code et la désignation sont obligatoires.");
        try (Connection c = conn()) {
            try (PreparedStatement chk = c.prepareStatement("SELECT 1 FROM produit WHERE code=? AND id_produit<>?")) {
                chk.setString(1, code); chk.setInt(2, id);
                if (chk.executeQuery().next()) throw new ApiException(400, "Ce code existe déjà.");
            }
            String unite = str(in.get("unite"));
            int pa = toInt(in.get("pa"));
            int seuil = toInt(in.get("seuil"));
            int cat = toInt(in.get("cat"));
            int pv = Math.max(0, toInt(in.get("pv")));
            if (id > 0) {
                try (PreparedStatement up = c.prepareStatement("UPDATE produit SET code=?,designation=?,unite=?,prix_achat=?,seuil_minimal=?,id_categorie=? WHERE id_produit=?")) {
                    up.setString(1, code); up.setString(2, des); up.setString(3, unite);
                    up.setInt(4, pa); up.setInt(5, seuil); up.setInt(6, cat); up.setInt(7, id);
                    up.executeUpdate();
                }
                if (isAdmin(u)) {
                    try (PreparedStatement upv = c.prepareStatement("UPDATE produit SET prix_vente=? WHERE id_produit=?")) {
                        upv.setInt(1, pv); upv.setInt(2, id); upv.executeUpdate();
                    }
                }
            } else {
                try (PreparedStatement ins = c.prepareStatement("INSERT INTO produit(code,designation,unite,prix_achat,seuil_minimal,id_categorie,prix_vente) VALUES(?,?,?,?,?,?,?)")) {
                    ins.setString(1, code); ins.setString(2, des); ins.setString(3, unite);
                    ins.setInt(4, pa); ins.setInt(5, seuil); ins.setInt(6, cat); ins.setInt(7, pv);
                    ins.executeUpdate();
                }
            }
        }
    }

    private static int stockOf(Connection c, int pid) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement("SELECT COALESCE(SUM(IF(type_mouvement='entree',quantite,-quantite)),0) s FROM stock WHERE id_produit=?")) {
            ps.setInt(1, pid);
            try (ResultSet rs = ps.executeQuery()) { return rs.next() ? rs.getInt("s") : 0; }
        }
    }

    private static void insertMove(Connection c, String type, int pid, int qt, int rest, int uid, Integer vid) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement("INSERT INTO stock(date_mouvement,type_mouvement,quantite,quantite_restante,id_produit,id_utilisateur,id_vente) VALUES(?,?,?,?,?,?,?)")) {
            ps.setString(1, utcNowStr()); ps.setString(2, type); ps.setInt(3, qt); ps.setInt(4, rest);
            ps.setInt(5, pid); ps.setInt(6, uid);
            if (vid == null) ps.setNull(7, Types.INTEGER); else ps.setInt(7, vid);
            ps.executeUpdate();
        }
    }

    private static void stockEntry(UserInfo u, Map in) throws SQLException {
        allow(canStock(u));
        int pid = toInt(in.get("pid"));
        int qt = toInt(in.get("q"));
        int pu = Math.max(0, toInt(in.get("pu")));
        if (qt <= 0) throw new ApiException(400, "La quantité doit être supérieure à zéro.");
        try (Connection c = conn()) {
            try (PreparedStatement chk = c.prepareStatement("SELECT 1 FROM produit WHERE id_produit=?")) {
                chk.setInt(1, pid);
                if (!chk.executeQuery().next()) throw new ApiException(400, "Produit introuvable.");
            }
            try (PreparedStatement up = c.prepareStatement("UPDATE produit SET prix_achat=? WHERE id_produit=?")) {
                up.setInt(1, pu); up.setInt(2, pid); up.executeUpdate();
            }
            insertMove(c, "entree", pid, qt, stockOf(c, pid) + qt, u.id(), null);
        }
    }

    private static void saveClient(UserInfo u, Map in) throws SQLException {
        allow(canSell(u));
        int id = toInt(in.get("id"));
        String nom = str(in.get("nom")).trim();
        String tel = str(in.get("tel")).trim();
        if (nom.isEmpty() || tel.isEmpty()) throw new ApiException(400, "Le nom et le téléphone sont obligatoires.");
        String prenom = str(in.get("prenom")).trim();
        String adr = str(in.get("adr"));
        int plafond = Math.max(0, toInt(in.get("plafond")));
        try (Connection c = conn()) {
            if (id > 0) {
                try (PreparedStatement up = c.prepareStatement("UPDATE client SET nom=?,prenom=?,telephone=?,adresse=?,plafond=? WHERE id_client=?")) {
                    up.setString(1, nom); up.setString(2, prenom); up.setString(3, tel); up.setString(4, adr); up.setInt(5, plafond); up.setInt(6, id); up.executeUpdate();
                }
            } else {
                try (PreparedStatement ins = c.prepareStatement("INSERT INTO client(nom,prenom,telephone,adresse,plafond) VALUES(?,?,?,?,?)")) {
                    ins.setString(1, nom); ins.setString(2, prenom); ins.setString(3, tel); ins.setString(4, adr); ins.setInt(5, plafond); ins.executeUpdate();
                }
            }
        }
    }

    private static void archiveClient(UserInfo u, int id) throws SQLException {
        allow(canSell(u));
        try (Connection c = conn(); PreparedStatement ps = c.prepareStatement("UPDATE client SET actif=0 WHERE id_client=?")) {
            ps.setInt(1, id); ps.executeUpdate();
        }
    }

    private static int soldeOf(Connection c, int cid) throws SQLException {
        String sql = "SELECT (SELECT COALESCE(SUM(montant_total),0) FROM vente WHERE id_client=? AND mode_paiement='credit' AND statut='validee')-"
                   + "(SELECT COALESCE(SUM(montant),0) FROM paiement WHERE id_client=?) s";
        try (PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setInt(1, cid); ps.setInt(2, cid);
            try (ResultSet rs = ps.executeQuery()) { return rs.next() ? rs.getInt("s") : 0; }
        }
    }

    private static boolean retardOf(Connection c, int cid) throws SQLException {
        if (soldeOf(c, cid) <= 0) return false;
        try (PreparedStatement ps = c.prepareStatement("SELECT MIN(date_vente) d FROM vente WHERE id_client=? AND mode_paiement='credit' AND statut='validee'")) {
            ps.setInt(1, cid);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return false;
                Timestamp ts = rs.getTimestamp("d");
                return ts != null && ts.toInstant().isBefore(Instant.now().minusSeconds(30L * 86400L));
            }
        }
    }

    private static void payClient(UserInfo u, Map in) throws SQLException {
        allow(canSell(u));
        int cid = toInt(in.get("cid"));
        try (Connection c = conn()) {
            int m = Math.min(toInt(in.get("m")), soldeOf(c, cid));
            if (m <= 0) throw new ApiException(400, "Montant invalide.");
            try (PreparedStatement ps = c.prepareStatement("INSERT INTO paiement(id_client,montant,date_paiement,id_utilisateur) VALUES(?,?,?,?)")) {
                ps.setInt(1, cid); ps.setInt(2, m); ps.setString(3, utcNowStr()); ps.setInt(4, u.id()); ps.executeUpdate();
            }
        }
    }

    private static int createSale(UserInfo u, Map in) throws SQLException {
        allow(canSell(u));
        int cid = toInt(in.get("cid"));
        int mid = toInt(in.get("id_mode"));
        int r = toInt(in.get("remise"));
        Object rawLi = in.get("lignes");
        if (!(rawLi instanceof List)) throw new ApiException(400, "Ajoutez au moins un produit.");
        List li = (List) rawLi;
        if (li.isEmpty()) throw new ApiException(400, "Ajoutez au moins un produit.");
        if (r < 0 || r > (isAdmin(u) ? 100 : 10)) throw new ApiException(400, "Remise non autorisée (maximum 10 % pour votre profil).");

        try (Connection c = conn()) {
            String nomMode;
            boolean estCredit;
            try (PreparedStatement mps = c.prepareStatement("SELECT nom_mode,est_credit FROM mode_paiement WHERE id_mode=? AND actif=1")) {
                mps.setInt(1, mid);
                try (ResultSet rs = mps.executeQuery()) {
                    if (!rs.next()) throw new ApiException(400, "Mode de paiement invalide.");
                    nomMode = str(rs.getString("nom_mode"));
                    estCredit = rs.getInt("est_credit") == 1;
                }
            }
            String mode = estCredit ? "credit" : "comptant";
            int plafond;
            try (PreparedStatement cps = c.prepareStatement("SELECT plafond FROM client WHERE id_client=? AND actif=1")) {
                cps.setInt(1, cid);
                try (ResultSet rs = cps.executeQuery()) {
                    if (!rs.next()) throw new ApiException(400, "Client introuvable.");
                    plafond = rs.getInt("plafond");
                }
            }

            c.setAutoCommit(false);
            try {
                long sub = 0;
                List lines = new ArrayList();
                for (Object item : li) {
                    if (!(item instanceof Map)) throw new ApiException(400, "Ligne de vente invalide.");
                    Map l = (Map) item;
                    int pid = toInt(l.get("pid"));
                    int qt = toInt(l.get("q"));
                    if (qt <= 0) throw new ApiException(400, "Quantité invalide.");
                    String des;
                    int pv;
                    try (PreparedStatement pps = c.prepareStatement("SELECT designation,prix_vente FROM produit WHERE id_produit=? FOR UPDATE")) {
                        pps.setInt(1, pid);
                        try (ResultSet rs = pps.executeQuery()) {
                            if (!rs.next()) throw new ApiException(400, "Produit introuvable.");
                            des = str(rs.getString("designation"));
                            pv = rs.getInt("prix_vente");
                        }
                    }
                    int s = stockOf(c, pid);
                    if (qt > s) throw new ApiException(400, "Stock insuffisant pour " + des + " (disponible : " + s + ").");
                    lines.add(new int[]{pid, qt, pv, s - qt});
                    sub += (long) qt * pv;
                }
                int tot = (int) Math.round(sub * (1.0 - r / 100.0));
                if ("credit".equals(mode) && !isAdmin(u)) {
                    if (retardOf(c, cid)) throw new ApiException(400, "Ce client a un crédit en retard de plus de 30 jours : vente à crédit refusée.");
                    if (soldeOf(c, cid) + tot > plafond) throw new ApiException(400, "Plafond de crédit dépassé (" + plafond + " FCFA). Accord de l’administrateur requis.");
                }

                String now = utcNowStr();
                int vid;
                try (PreparedStatement vins = c.prepareStatement(
                        "INSERT INTO vente(reference,date_vente,mode_paiement,id_mode,remise,montant_total,statut,id_client,id_utilisateur) VALUES(?,?,?,?,?,?,'validee',?,?)",
                        Statement.RETURN_GENERATED_KEYS)) {
                    vins.setString(1, "T" + UUID.randomUUID().toString().substring(0, 8));
                    vins.setString(2, now); vins.setString(3, mode); vins.setInt(4, mid);
                    vins.setInt(5, r); vins.setInt(6, tot); vins.setInt(7, cid); vins.setInt(8, u.id());
                    vins.executeUpdate();
                    try (ResultSet keys = vins.getGeneratedKeys()) {
                        keys.next();
                        vid = keys.getInt(1);
                    }
                }
                try (PreparedStatement vref = c.prepareStatement("UPDATE vente SET reference=? WHERE id_vente=?")) {
                    vref.setString(1, String.format("V-%04d", vid)); vref.setInt(2, vid); vref.executeUpdate();
                }
                for (Object obj : lines) {
                    int[] l = (int[]) obj;
                    try (PreparedStatement cins = c.prepareStatement("INSERT INTO contenir(id_vente,id_produit,quantite,prix_unitaire) VALUES(?,?,?,?)")) {
                        cins.setInt(1, vid); cins.setInt(2, l[0]); cins.setInt(3, l[1]); cins.setInt(4, l[2]); cins.executeUpdate();
                    }
                    insertMove(c, "sortie", l[0], l[1], l[3], u.id(), vid);
                }
                try (PreparedStatement hins = c.prepareStatement("INSERT INTO historique_vente(id_vente,action,details,date_action,id_utilisateur) VALUES(?,?,?,?,?)")) {
                    hins.setInt(1, vid); hins.setString(2, "création"); hins.setString(3, nomMode + " - " + tot + " FCFA");
                    hins.setString(4, now); hins.setInt(5, u.id()); hins.executeUpdate();
                }
                c.commit();
                return vid;
            } catch (Exception ex) {
                c.rollback();
                throw ex;
            } finally {
                c.setAutoCommit(true);
            }
        }
    }

    private static void cancelSale(UserInfo u, int id, String mo) throws SQLException {
        allow(isAdmin(u));
        if (mo.isEmpty()) throw new ApiException(400, "Indiquez le motif de l’annulation.");
        try (Connection c = conn()) {
            try (PreparedStatement chk = c.prepareStatement("SELECT 1 FROM vente WHERE id_vente=? AND statut='validee'")) {
                chk.setInt(1, id);
                if (!chk.executeQuery().next()) throw new ApiException(400, "Cette vente ne peut pas être annulée.");
            }
            c.setAutoCommit(false);
            try {
                String now = utcNowStr();
                try (PreparedStatement up = c.prepareStatement("UPDATE vente SET statut='annulee',motif_annulation=?,annule_par=?,date_annulation=? WHERE id_vente=?")) {
                    up.setString(1, mo); up.setInt(2, u.id()); up.setString(3, now); up.setInt(4, id); up.executeUpdate();
                }
                List items = new ArrayList();
                try (PreparedStatement lps = c.prepareStatement("SELECT id_produit,quantite FROM contenir WHERE id_vente=?")) {
                    lps.setInt(1, id);
                    try (ResultSet rs = lps.executeQuery()) {
                        while (rs.next()) items.add(new int[]{rs.getInt("id_produit"), rs.getInt("quantite")});
                    }
                }
                for (Object obj : items) {
                    int[] it = (int[]) obj;
                    insertMove(c, "entree", it[0], it[1], stockOf(c, it[0]) + it[1], u.id(), id);
                }
                try (PreparedStatement hins = c.prepareStatement("INSERT INTO historique_vente(id_vente,action,details,date_action,id_utilisateur) VALUES(?,?,?,?,?)")) {
                    hins.setInt(1, id); hins.setString(2, "annulation"); hins.setString(3, mo);
                    hins.setString(4, now); hins.setInt(5, u.id()); hins.executeUpdate();
                }
                c.commit();
            } catch (Exception ex) {
                c.rollback();
                throw ex;
            } finally {
                c.setAutoCommit(true);
            }
        }
    }

    private static void saveCategory(UserInfo u, Map in) throws SQLException {
        allow(canStock(u));
        int id = toInt(in.get("id"));
        String nom = str(in.get("nom")).trim();
        if (nom.isEmpty()) throw new ApiException(400, "Le nom est obligatoire.");
        try (Connection c = conn()) {
            try (PreparedStatement chk = c.prepareStatement("SELECT 1 FROM categorie WHERE nom_categorie=? AND id_categorie<>?")) {
                chk.setString(1, nom); chk.setInt(2, id);
                if (chk.executeQuery().next()) throw new ApiException(400, "Cette catégorie existe déjà.");
            }
            if (id > 0) {
                try (PreparedStatement up = c.prepareStatement("UPDATE categorie SET nom_categorie=? WHERE id_categorie=?")) {
                    up.setString(1, nom); up.setInt(2, id); up.executeUpdate();
                }
            } else {
                try (PreparedStatement ins = c.prepareStatement("INSERT INTO categorie(nom_categorie) VALUES(?)")) {
                    ins.setString(1, nom); ins.executeUpdate();
                }
            }
        }
    }

    private static void deleteCategory(UserInfo u, int id) throws SQLException {
        allow(canStock(u));
        try (Connection c = conn()) {
            try (PreparedStatement chk = c.prepareStatement("SELECT 1 FROM produit WHERE id_categorie=?")) {
                chk.setInt(1, id);
                if (chk.executeQuery().next()) throw new ApiException(400, "Impossible : des produits utilisent cette catégorie.");
            }
            try (PreparedStatement del = c.prepareStatement("DELETE FROM categorie WHERE id_categorie=?")) {
                del.setInt(1, id); del.executeUpdate();
            }
        }
    }

    private static void saveUser(UserInfo u, Map in) throws SQLException {
        allow(isAdmin(u));
        int id = toInt(in.get("id"));
        String nom = str(in.get("nom")).trim();
        String login = str(in.get("login")).trim();
        String pw = str(in.get("pw"));
        String role = str(in.get("role")).trim();
        if (nom.isEmpty() || login.isEmpty() || (id == 0 && pw.isEmpty())) throw new ApiException(400, "Nom, identifiant et mot de passe sont obligatoires.");
        if (!VALID_ROLES.contains(role)) throw new ApiException(400, "Rôle invalide.");

        try (Connection c = conn()) {
            try (PreparedStatement chk = c.prepareStatement("SELECT 1 FROM utilisateur WHERE identifiant=? AND id_utilisateur<>?")) {
                chk.setString(1, login); chk.setInt(2, id);
                if (chk.executeQuery().next()) throw new ApiException(400, "Cet identifiant est déjà utilisé.");
            }
            if (id > 0) {
                try (PreparedStatement up = c.prepareStatement("UPDATE utilisateur SET nom=?,identifiant=?,role=? WHERE id_utilisateur=?")) {
                    up.setString(1, nom); up.setString(2, login); up.setString(3, role); up.setInt(4, id); up.executeUpdate();
                }
                if (!pw.isEmpty()) {
                    try (PreparedStatement upp = c.prepareStatement("UPDATE utilisateur SET mot_de_passe=? WHERE id_utilisateur=?")) {
                        upp.setString(1, hashPassword(pw)); upp.setInt(2, id); upp.executeUpdate();
                    }
                }
            } else {
                try (PreparedStatement ins = c.prepareStatement("INSERT INTO utilisateur(nom,prenom,identifiant,mot_de_passe,telephone,adresse,role,actif) VALUES(?,'',?,?,'','',?,1)")) {
                    ins.setString(1, nom); ins.setString(2, login); ins.setString(3, hashPassword(pw)); ins.setString(4, role); ins.executeUpdate();
                }
            }
        }
    }

    private static void changePassword(UserInfo u, String oldPw, String newPw) throws SQLException {
        if (newPw.length() < 6) throw new ApiException(400, "Le nouveau mot de passe doit contenir au moins 6 caractères.");
        try (Connection c = conn()) {
            String stored;
            try (PreparedStatement ps = c.prepareStatement("SELECT mot_de_passe FROM utilisateur WHERE id_utilisateur=?")) {
                ps.setInt(1, u.id());
                try (ResultSet rs = ps.executeQuery()) {
                    if (!rs.next()) throw new ApiException(401, "Utilisateur introuvable.");
                    stored = str(rs.getString("mot_de_passe"));
                }
            }
            boolean match = stored.startsWith("SHA256:") ? constantTimeEq(stored, hashPassword(oldPw)) : constantTimeEq(stored, oldPw);
            if (!match) throw new ApiException(400, "Ancien mot de passe incorrect.");
            try (PreparedStatement up = c.prepareStatement("UPDATE utilisateur SET mot_de_passe=? WHERE id_utilisateur=?")) {
                up.setString(1, hashPassword(newPw)); up.setInt(2, u.id()); up.executeUpdate();
            }
        }
    }

    private static void toggleUser(UserInfo u, int id) throws SQLException {
        allow(isAdmin(u));
        if (id == u.id()) throw new ApiException(400, "Vous ne pouvez pas désactiver votre propre compte.");
        try (Connection c = conn(); PreparedStatement ps = c.prepareStatement("UPDATE utilisateur SET actif=1-actif WHERE id_utilisateur=?")) {
            ps.setInt(1, id); ps.executeUpdate();
        }
    }

    private static String hashPassword(String pw) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] dig = md.digest(pw.getBytes(StandardCharsets.UTF_8));
            return "SHA256:" + HexFormat.of().formatHex(dig);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static boolean constantTimeEq(String a, String b) {
        return MessageDigest.isEqual(a.getBytes(StandardCharsets.UTF_8), b.getBytes(StandardCharsets.UTF_8));
    }

    private static long sqlDateToMs(Timestamp ts) {
        return ts == null ? 0L : ts.toInstant().toEpochMilli();
    }

    private static String utcNowStr() {
        return LocalDateTime.now(ZoneOffset.UTC).format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }

    private static String str(Object o) { return o == null ? "" : String.valueOf(o); }
    private static int toInt(Object o) {
        if (o == null) return 0;
        if (o instanceof Number n) return n.intValue();
        try { return Integer.parseInt(String.valueOf(o).trim()); } catch (Exception e) { return 0; }
    }

    private static void sendJson(HttpExchange ex, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        ex.sendResponseHeaders(status, bytes.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(bytes); }
    }

    static class ApiException extends RuntimeException {
        final int code;
        ApiException(int code, String msg) { super(msg); this.code = code; }
    }

    private static Map mapObj(Object... kv) {
        Map m = new LinkedHashMap();
        for (int i = 0; i < kv.length; i += 2) {
            m.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return m;
    }

    private static String jsonObj(Object... kv) {
        StringBuilder sb = new StringBuilder("{");
        for (int i = 0; i < kv.length; i += 2) {
            if (i > 0) sb.append(",");
            sb.append(jsonStr(String.valueOf(kv[i]))).append(":").append(toJsonVal(kv[i + 1]));
        }
        return sb.append("}").toString();
    }

    private static String toJsonVal(Object v) {
        if (v == null) return "null";
        if (v instanceof Boolean b) return b ? "true" : "false";
        if (v instanceof Number n) return n.toString();
        if (v instanceof Map m) {
            StringBuilder sb = new StringBuilder("{");
            boolean first = true;
            for (Object key : m.keySet()) {
                if (!first) sb.append(",");
                first = false;
                sb.append(jsonStr(String.valueOf(key))).append(":").append(toJsonVal(m.get(key)));
            }
            return sb.append("}").toString();
        }
        if (v instanceof Iterable it) {
            StringBuilder sb = new StringBuilder("[");
            boolean first = true;
            for (Object item : it) {
                if (!first) sb.append(",");
                first = false;
                sb.append(toJsonVal(item));
            }
            return sb.append("]").toString();
        }
        return jsonStr(String.valueOf(v));
    }

    private static String jsonStr(String s) {
        StringBuilder sb = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            switch (ch) {
                case '\\' -> sb.append("\\\\");
                case '\"' -> sb.append("\\\"");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> sb.append(ch);
            }
        }
        return sb.append("\"").toString();
    }

    private static Map parseJsonObject(String s) {
        if (s == null || s.isBlank()) return new HashMap();
        Object parsed = new JsonParser(s).parseValue();
        return (parsed instanceof Map) ? (Map) parsed : new HashMap();
    }

    static class JsonParser {
        private final String s;
        private int i = 0;
        JsonParser(String s) { this.s = s; }
        Object parseValue() {
            skipWs();
            if (i >= s.length()) return null;
            char c = s.charAt(i);
            if (c == '{') return parseObj();
            if (c == '[') return parseArr();
            if (c == '"') return parseStr();
            if (c == 't') { i += 4; return Boolean.TRUE; }
            if (c == 'f') { i += 5; return Boolean.FALSE; }
            if (c == 'n') { i += 4; return null; }
            return parseNum();
        }
        Map parseObj() {
            i++; skipWs();
            Map map = new LinkedHashMap();
            if (i < s.length() && s.charAt(i) == '}') { i++; return map; }
            while (i < s.length()) {
                skipWs();
                String k = parseStr();
                skipWs();
                if (i < s.length() && s.charAt(i) == ':') i++;
                Object v = parseValue();
                map.put(k, v);
                skipWs();
                if (i < s.length() && s.charAt(i) == ',') { i++; continue; }
                if (i < s.length() && s.charAt(i) == '}') { i++; break; }
            }
            return map;
        }
        List parseArr() {
            i++; skipWs();
            List list = new ArrayList();
            if (i < s.length() && s.charAt(i) == ']') { i++; return list; }
            while (i < s.length()) {
                list.add(parseValue());
                skipWs();
                if (i < s.length() && s.charAt(i) == ',') { i++; continue; }
                if (i < s.length() && s.charAt(i) == ']') { i++; break; }
            }
            return list;
        }
        String parseStr() {
            i++;
            StringBuilder sb = new StringBuilder();
            while (i < s.length()) {
                char c = s.charAt(i++);
                if (c == '"') break;
                if (c == '\\' && i < s.length()) {
                    char e = s.charAt(i++);
                    sb.append(switch (e) {
                        case 'n' -> '\n';
                        case 'r' -> '\r';
                        case 't' -> '\t';
                        default -> e;
                    });
                } else sb.append(c);
            }
            return sb.toString();
        }
        Number parseNum() {
            int start = i;
            boolean fp = false;
            while (i < s.length()) {
                char c = s.charAt(i);
                if (c == '.' || c == 'e' || c == 'E') fp = true;
                if (Character.isDigit(c) || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E') i++;
                else break;
            }
            String num = s.substring(start, i);
            try { return fp ? Double.parseDouble(num) : Integer.parseInt(num); }
            catch (Exception e) { return 0; }
        }
        void skipWs() { while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++; }
    }
}