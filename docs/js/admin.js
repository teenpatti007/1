/* MovieHub admin panel logic (Firebase compat SDK). */
(function () {
  "use strict";

  if (typeof firebase === "undefined" || typeof firebaseConfig === "undefined") {
    var el = document.getElementById("signinToast");
    if (el) {
      el.className = "toast err";
      el.textContent = "Firebase failed to load. Open this page over the internet (it needs the Firebase CDN).";
    }
    return;
  }

  firebase.initializeApp(firebaseConfig);
  var auth = firebase.auth();
  var db = firebase.database();

  var $ = function (id) { return document.getElementById(id); };

  function toast(el, msg, kind) {
    el.className = "toast " + (kind || "ok");
    el.textContent = msg;
  }

  // ---- auth state ----
  auth.onAuthStateChanged(function (user) {
    if (user) {
      $("signin").classList.add("hidden");
      $("admin").classList.remove("hidden");
      loadCodes();
    } else {
      $("signin").classList.remove("hidden");
      $("admin").classList.add("hidden");
    }
  });

  $("signinBtn").addEventListener("click", function () {
    var email = $("email").value.trim();
    var password = $("password").value;
    auth.signInWithEmailAndPassword(email, password)
      .then(function () { toast($("signinToast"), "Signed in.", "ok"); })
      .catch(function (err) { toast($("signinToast"), err.message, "err"); });
  });

  $("signoutBtn").addEventListener("click", function () {
    auth.signOut();
  });

  // ---- generate a 4-digit code ----
  $("genBtn").addEventListener("click", function () {
    var code = String(Math.floor(1000 + Math.random() * 9000)); // 1000-9999
    db.ref("passcodes/" + code).once("value").then(function (snap) {
      if (snap.exists()) {
        toast($("adminToast"), "Code " + code + " already exists — try again.", "err");
        return;
      }
      db.ref("passcodes/" + code).set({ active: true, created: Date.now() })
        .then(function () {
          toast($("adminToast"), "Generated code: " + code, "ok");
          loadCodes();
        })
        .catch(function (err) { toast($("adminToast"), err.message, "err"); });
    });
  });

  $("refreshBtn").addEventListener("click", loadCodes);

  // ---- list codes ----
  function loadCodes() {
    db.ref("passcodes").once("value").then(function (snap) {
      var obj = snap.val() || {};
      var rows = $("codeRows");
      var keys = Object.keys(obj).sort();
      if (!keys.length) {
        rows.innerHTML = '<tr><td colspan="5" class="muted">No codes yet.</td></tr>';
        return;
      }
      rows.innerHTML = "";
      keys.forEach(function (code) {
        var c = obj[code] || {};
        var active = c.active !== false;
        var mac = c.mac || "—";
        var activated = c.activated ? new Date(c.activated).toLocaleString() : "—";
        var tr = document.createElement("tr");
        tr.innerHTML =
          "<td><b>" + code + "</b></td>" +
          '<td><span class="pill ' + (active ? "on" : "off") + '">' +
            (active ? "Active" : "Revoked") + "</span></td>" +
          '<td class="mono">' + mac + "</td>" +
          "<td class=" + '"muted small">' + activated + "</td>" +
          "<td>" +
            (active
              ? '<button class="btn secondary" data-revoke="' + code + '">Revoke</button>'
              : '<button class="btn secondary" data-del="' + code + '">Delete</button>') +
          "</td>";
        rows.appendChild(tr);
      });
      Array.prototype.forEach.call(rows.querySelectorAll("[data-revoke]"), function (b) {
        b.addEventListener("click", function () { revoke(b.getAttribute("data-revoke")); });
      });
      Array.prototype.forEach.call(rows.querySelectorAll("[data-del]"), function (b) {
        b.addEventListener("click", function () { del(b.getAttribute("data-del")); });
      });
    });
  }

  function revoke(code) {
    db.ref("passcodes/" + code).update({ active: false }).then(loadCodes);
  }
  function del(code) {
    db.ref("passcodes/" + code).remove().then(loadCodes);
  }
})();
