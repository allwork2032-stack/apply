import express from "express";
import mongoose from "mongoose";
import bodyParser from "body-parser";
import multer from "multer";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = 3000;

// ✅ MongoDB কানেকশন (নিজের ডাটাবেস URL বসাও)
mongoose.connect("mongodb://127.0.0.1:27017/job_applications", {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Schema বানানো
const applicantSchema = new mongoose.Schema({
  name: String,
  email: String,
  phone: String,
  position: String,
  cvPath: String,
});

const Applicant = mongoose.model("Applicant", applicantSchema);

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"));
app.use("/uploads", express.static("uploads"));

// File upload setup
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, "uploads/"),
  filename: (req, file, cb) =>
    cb(null, Date.now() + path.extname(file.originalname)),
});
const upload = multer({ storage });

// Route: আবেদন ফর্ম
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Route: ফর্ম সাবমিশন
app.post("/apply", upload.single("cv"), async (req, res) => {
  const applicant = new Applicant({
    name: req.body.name,
    email: req.body.email,
    phone: req.body.phone,
    position: req.body.position,
    cvPath: req.file ? req.file.path : null,
  });

  await applicant.save();
  res.send("✅ আপনার চাকুরীর আবেদন জমা হয়েছে এবং ডাটাবেসে সেভ হয়েছে।");
});

// Route: অ্যাডমিন পেজ (সকল আবেদনকারীর লিস্ট দেখাবে)
app.get("/admin", async (req, res) => {
  const applicants = await Applicant.find();
  let html = `
    <h1>📋 আবেদনকারীর তালিকা</h1>
    <table border="1" cellspacing="0" cellpadding="8">
      <tr>
        <th>নাম</th>
        <th>ইমেইল</th>
        <th>মোবাইল</th>
        <th>পদ</th>
        <th>সিভি</th>
      </tr>
  `;

  applicants.forEach((app) => {
    html += `
      <tr>
        <td>${app.name}</td>
        <td>${app.email}</td>
        <td>${app.phone}</td>
        <td>${app.position}</td>
        <td>${app.cvPath ? `<a href="/${app.cvPath}" target="_blank">ডাউনলোড</a>` : "N/A"}</td>
      </tr>
    `;
  });

  html += `</table>`;
  res.send(html);
});

// Start server
app.listen(port, () => {
  console.log(`🚀 Server is running on http://localhost:${port}`);
});
