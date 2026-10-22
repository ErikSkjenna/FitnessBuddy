const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const factory = require('../netlify-site/store.js');
const fixedClock = () => new Date(2026,9,22,12,0);
function fixture() {
  const values = new Map();
  const storage = {getItem: key => values.get(key) ?? null, setItem: (key,value) => values.set(key,value)};
  return {values, storage, store:factory(storage, fixedClock)};
}
const profile = {name:'Tester', activity:'Running', slot:'Weekend mornings', level:'Intermediate', area:'Downtown'};
const meetup = {title:'Test session', activity:'Gym', location:'Public lobby', day:'2026-10-25', time:'18:00', capacity:3};
test('New visitor gets explained demo matches', () => {
  const {store} = fixture(); const state = store.request('/api/state');
  assert.equal(state.matches.length,4); assert.equal(state.matches[0].score,4);
  assert.equal(state.matches[0].name,'Alex (demo)');
  assert.equal(state.matches[0].reasons.length,4);
});
test('Profile save reranks and persists across store instances', () => {
  const {store,storage} = fixture(); store.request('/api/profile',profile);
  const state = factory(storage,fixedClock).request('/api/state');
  assert.equal(state.profile.name,'Tester'); assert.equal(state.matches[0].name,'Sam (demo)');
});
test('Invalid profile leaves previous state intact', () => {
  const {store} = fixture(); const before=store.request('/api/state');
  assert.throws(() => store.request('/api/profile',{...profile,activity:'Unknown'}));
  assert.deepEqual(store.request('/api/state'),before);
});
test('Creating a meetup enrolls its creator and persists', () => {
  const {store,storage} = fixture(); const {id} = store.request('/api/meetups',meetup);
  const event=factory(storage,fixedClock).request('/api/state').meetups.find(e=>e.id===id);
  assert.equal(event.title,meetup.title); assert.equal(event.attendees,1); assert.equal(event.joined,true);
});
test('Repeat join and leave actions do not duplicate attendance', () => {
  const {store}=fixture();
  for(let i=0;i<2;i++) store.request('/api/meetups/1/join',{});
  assert.equal(store.request('/api/state').meetups[0].attendees,2);
  for(let i=0;i<2;i++) store.request('/api/meetups/1/leave',{});
  assert.equal(store.request('/api/state').meetups[0].attendees,1);
});
test('A full meetup rejects joining', () => {
  const {store,storage,values}=fixture(); store.request('/api/state');
  const key=[...values.keys()][0]; const data=JSON.parse(storage.getItem(key));
  data.meetups[0].attendees=4; storage.setItem(key,JSON.stringify(data));
  assert.throws(()=>store.request('/api/meetups/1/join',{}),/full/);
});
test('Expired meetup and missing meetup reject joining', () => {
  const {store,storage}=fixture(); store.request('/api/state');
  const later=factory(storage,()=>new Date(2027,0,1));
  assert.throws(()=>later.request('/api/meetups/1/join',{}),/ended/);
  assert.throws(()=>store.request('/api/meetups/999/join',{}),/not found/);
});
test('Invalid meetup fields do not create records', () => {
  const {store}=fixture();
  for(const change of [{day:'2027-02-30'},{day:'2026-10-21'},{time:'25:00'},{capacity:2.5},{capacity:true},{capacity:21},{title:''}])
    assert.throws(()=>store.request('/api/meetups',{...meetup,...change}));
  assert.equal(store.request('/api/state').meetups.length,1);
});
test('Separate browsers have independent demo state', () => {
  const a=fixture().store, b=fixture().store; a.request('/api/profile',profile);
  assert.equal(b.request('/api/state').profile.name,'You');
});
test('Damaged saved data is reported without deletion', () => {
  const {store,storage,values}=fixture(); store.request('/api/state'); const key=[...values.keys()][0];
  storage.setItem(key,'broken'); assert.throws(()=>store.request('/api/state'),/could not be read/);
  assert.equal(storage.getItem(key),'broken');
});
test('Storage write failure is reported and does not claim success', () => {
  const store=factory({getItem:()=>null,setItem:()=>{throw new Error('Quota');}},fixedClock);
  assert.throws(()=>store.request('/api/state'),/could not save/);
});
test('Blocked storage is reported', () => {
  const store=factory({getItem:()=>{throw new Error('Blocked');}},fixedClock);
  assert.throws(()=>store.request('/api/state'),/storage is blocked/);
});
test('Public entry point references existing static assets', () => {
  const root=path.join(__dirname,'../netlify-site'); const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  for(const match of html.matchAll(/(?:src|href)="(\/[^"#]+)"/g)) assert.ok(fs.existsSync(path.join(root,match[1])));
  assert.ok(html.indexOf('store.js')<html.indexOf('app.js'));
});
test('Netlify form declares consent, spam trap, identity, and success page', () => {
  const root=path.join(__dirname,'../netlify-site'); const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  assert.match(html,/name="pilot-interest" method="POST"/);
  assert.match(html,/data-netlify="true"/); assert.match(html,/name="form-name" value="pilot-interest"/);
  assert.match(html,/netlify-honeypot="bot-field"/); assert.match(html,/name="consent" type="checkbox" required/);
  assert.ok(fs.existsSync(path.join(root,'thank-you.html')));
});
test('Static app has no dependency on a running Python API', () => {
  const js=fs.readFileSync(path.join(__dirname,'../netlify-site/app.js'),'utf8');
  assert.doesNotMatch(js,/fetch\(/); assert.match(js,/demoStore\.request/);
});
