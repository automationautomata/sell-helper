const express = require("express");
const cors = require("cors");
const multer = require("multer");
const fs = require("fs");
const path = require("path");
const os = require("os");

const app = express();

const TEMP_DIR = fs.mkdtempSync(
  path.join(os.tmpdir(), "mock-api-uploads-")
);


const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, TEMP_DIR);
  },
  filename: (_, file, cb) => {
    cb(
      null,
      `${Date.now()}-${Math.random().toString(36).slice(2)}${path.extname(file.originalname)}`
    );
  },
});

const upload = multer({ storage });

app.use(cors());
app.use(express.json());

app.post("/auth/login", (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ error: "Missing credentials" });
  }

  res.json({
    token: "mock-jwt-token-123",
    ttl: 1200,
  });
});

const auth = (req, res, next) => {
  const header = req.headers.authorization;
  if (!header || !header.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
};

app.post(
  "/product/:marketplace/recognize",
  auth,
  upload.single("image"),
  (_, res) => {
    res.json({
      product_name: "Wireless Headphones",
      categories: ["Electronics", "Audio", "Headphones"],
    });
  }
);

app.post("/product/:marketplace/aspects", auth, (_, res) => {
  res.json({
    metadata: {
      description: "High quality wireless headphones",
    },
    metadata_type: "Metadata",
    product: {
      aspects: {
        Brand: "Sony",
        Color: "Black",
        Connectivity: "Bluetooth",
        Condition: "New",
      },
      required: ["Brand", "Color", "Connectivity"],
    },
  });
});

app.post(
  "/product/:marketplace/publish",
  auth,
  upload.array("images"),
  (req, res) => {
    const _ = JSON.parse(req.body.item);
    res.json({ status: "success" });
  }
);

app.get(
  "/settings/:marketplace",
  auth,
  (req, res) => {
    res.json({settings: {"test": ["value 1", "value 2"], "other": ["another"]} });
  }
);

const cleanup = () => {
  console.log("Cleaning temp dir...");
  fs.rmSync(TEMP_DIR, { recursive: true, force: true });
  process.exit(0);
};

process.on("SIGINT", cleanup);
process.on("SIGTERM", cleanup);

app.listen(3000, () => console.log("Running on http://localhost:3000"));
