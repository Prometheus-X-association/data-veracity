// Connect to the project database 'dva'
mongoose.connect(process.env.MONGO_URL || 'mongodb://localhost:27017/dva', {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

// Schema for the 'requests' collection
const attReqSchema = new mongoose.Schema({
  id: String,
  vlaId: String,
  data: Buffer,
  attesterID: String,
  callbackURL: String,
  mapping: Object,
  successful: Boolean,
  date: Date
}, { collection: 'requests' });

const AttReq = mongoose.model('AttReq', attReqSchema);

const app = express();
app.use(cors());
app.use(express.json());

// Expose endpoints
app.get('/api/issued', async (req, res) => {
  const docs = await AttReq.find({ successful: true }).sort('-date');
  res.json(docs);
});

app.get('/api/requested', async (req, res) => {
  const docs = await AttReq.find().sort('-date');
  res.json(docs);
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Dashboard API on http://localhost:${PORT}`));