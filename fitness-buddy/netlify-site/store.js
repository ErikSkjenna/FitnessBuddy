/* The published prototype stores demo progress only in this browser. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory;
  else root.createFitnessStore = factory;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (storage, clock = () => new Date()) {
  const KEY = 'fitness-buddy:demo:v1';
  const choices = {
    activity: ['Gym', 'Running', 'Fitness classes'],
    slot: ['Weekday mornings', 'Weekday evenings', 'Weekend mornings'],
    level: ['Beginner', 'Intermediate', 'Experienced'],
    area: ['Campus', 'Downtown', 'West Ottawa']
  };
  const partners = [
    { id: 2, name: 'Alex (demo)', activity: 'Gym', slot: 'Weekday evenings', level: 'Beginner', area: 'Campus' },
    { id: 3, name: 'Sam (demo)', activity: 'Running', slot: 'Weekend mornings', level: 'Intermediate', area: 'Downtown' },
    { id: 4, name: 'Jordan (demo)', activity: 'Fitness classes', slot: 'Weekday evenings', level: 'Beginner', area: 'Campus' },
    { id: 5, name: 'Casey (demo)', activity: 'Gym', slot: 'Weekday mornings', level: 'Experienced', area: 'West Ottawa' }
  ];
  const dayString = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  function text(data, key, max = 80) {
    const value = data[key];
    if (typeof value !== 'string' || !value.trim() || value.trim().length > max) throw new Error(`${key}: enter 1–${max} characters.`);
    return value.trim();
  }
  function choice(data, key) {
    const value = text(data, key);
    if (!choices[key].includes(value)) throw new Error(`${key}: select one of the listed options.`);
    return value;
  }
  function validDay(value) {
    return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
      !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0,10) === value;
  }
  function profile(data) {
    return {id: 1, name: text(data, 'name', 40), ...Object.fromEntries(Object.keys(choices).map(key => [key, choice(data, key)]))};
  }
  function seed() {
    const day = clock(); day.setDate(day.getDate() + 3);
    return { version: 1,
      profile: profile({name:'You', activity:'Gym', slot:'Weekday evenings', level:'Beginner', area:'Campus'}),
      meetups: [{id:1, title:'First gym session', activity:'Gym', location:'Campus recreation lobby (demo)',
        day:dayString(day), time:'18:00', capacity:4, attendees:1, joined:false, seeded:1}]
    };
  }
  function save(data) {
    try { storage.setItem(KEY, JSON.stringify(data)); }
    catch { throw new Error('Your browser could not save progress. Allow site storage or free some space, then try again.'); }
  }
  function load() {
    let raw;
    try { raw = storage.getItem(KEY); }
    catch { throw new Error('Site storage is blocked. Allow browser storage to use this demo.'); }
    if (raw === null) { const data = seed(); save(data); return data; }
    try {
      const data = JSON.parse(raw);
      if (data.version !== 1 || !Array.isArray(data.meetups)) throw new Error();
      data.profile = profile(data.profile);
      const ids = new Set();
      for (const event of data.meetups) {
        text(event, 'title'); text(event, 'location', 120); choice(event, 'activity');
        if (!Number.isSafeInteger(event.id) || event.id < 1 || ids.has(event.id) ||
            !validDay(event.day) || !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(event.time) ||
            !Number.isInteger(event.capacity) || event.capacity < 2 || event.capacity > 20 ||
            !Number.isInteger(event.attendees) || event.attendees < 0 || event.attendees > event.capacity ||
            typeof event.joined !== 'boolean' || (event.joined && event.attendees < 1)) throw new Error();
        ids.add(event.id);
      }
      return data;
    } catch { throw new Error('Saved demo data could not be read. Clear this site’s browser storage to start a fresh demo.'); }
  }
  return {
    request(path, input) {
      const data = load();
      if (path === '/api/state' && input === undefined) {
        const labels = {activity:'Same activity', slot:'Shared availability', area:'Same area', level:'Same experience level'};
        const matches = partners.map(person => {
          const reasons = Object.entries(labels).filter(([key]) => person[key] === data.profile[key]).map(([, label]) => label);
          return {...person, reasons, score:reasons.length};
        }).sort((a,b) => b.score-a.score || a.name.localeCompare(b.name));
        return {profile:data.profile, matches, meetups:data.meetups.sort((a,b) => (a.day+a.time).localeCompare(b.day+b.time) || a.id-b.id)};
      }
      if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Invalid request.');
      let result;
      if (path === '/api/profile') {
        data.profile = profile(input);
        result = {message:'Profile saved in this browser. Matches updated.'};
      } else if (path === '/api/meetups') {
        const event = {title:text(input,'title'), activity:choice(input,'activity'), location:text(input,'location',120),
          day:text(input,'day',10), time:text(input,'time',5), capacity:input.capacity};
        if (!validDay(event.day) || event.day <= dayString(clock())) throw new Error('Choose a valid date after today.');
        if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(event.time)) throw new Error('Enter a valid time.');
        if (!Number.isInteger(event.capacity) || event.capacity < 2 || event.capacity > 20) throw new Error('Group size must be a whole number from 2 to 20.');
        event.id = data.meetups.reduce((max,item) => Math.max(max,item.id),0)+1;
        data.meetups.push({...event, attendees:1, joined:true, seeded:0});
        result = {id:event.id, message:'Demo meetup created in this browser. You are attending.'};
      } else {
        const action = /^\/api\/meetups\/(\d+)\/(join|leave)$/.exec(path);
        if (!action) throw new Error('Unknown action.');
        const event = data.meetups.find(item => item.id === Number(action[1]));
        if (!event) throw new Error('Meetup not found.');
        if (action[2] === 'join') {
          if (new Date(`${event.day}T${event.time}`) <= clock()) throw new Error('This meetup has ended.');
          if (!event.joined && event.attendees >= event.capacity) throw new Error('This meetup is full.');
          if (!event.joined) { event.joined = true; event.attendees++; }
          result = {message:'Joined demo meetup in this browser.'};
        } else {
          if (event.joined) { event.joined = false; event.attendees--; }
          result = {message:'Left demo meetup.'};
        }
      }
      save(data);
      return result;
    }
  };
});
