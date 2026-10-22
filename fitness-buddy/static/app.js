'use strict';
let state;
const $ = selector => document.querySelector(selector);
function status(message, error = false) {
  $('#status').textContent = message;
  $('#status').classList.toggle('error', error);
}
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed. Please try again.');
  return result;
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text; // User input is never inserted as HTML.
  if (className) node.className = className;
  return node;
}
function renderMatches() {
  const target = $('#matches'); target.replaceChildren();
  const people = state.matches.filter(p => $('#match-filter').value !== 'schedule' || p.slot === state.profile.slot);
  if (!people.length) target.append(element('p', 'No demo partners share that schedule. Try another time or show all partners.'));
  for (const person of people) {
    const card = element('article', undefined, 'card');
    card.append(element('div', person.name[0], 'avatar'), element('h3', person.name),
      element('span', `${person.score}/4 preferences in common`, 'badge'),
      element('p', `${person.activity} · ${person.level} · ${person.area}`), element('p', person.slot));
    const reasons = element('ul');
    for (const reason of person.reasons) reasons.append(element('li', reason));
    if (!person.reasons.length) reasons.append(element('li', 'No shared preferences yet'));
    card.append(reasons); target.append(card);
  }
}
function renderEvents() {
  const target = $('#events'); target.replaceChildren();
  if (!state.meetups.length) target.append(element('p', 'No meetups yet. Create the first one.'));
  for (const event of state.meetups) {
    const card = element('article', undefined, 'card');
    card.append(element('span', event.seeded ? 'FICTIONAL DEMO SESSION' : 'YOUR LOCAL SESSION', 'badge'),
      element('h3', event.title), element('p', `${event.day} · ${event.time} · ${event.activity}`),
      element('p', event.location), element('p', `${event.attendees}/${event.capacity} attending${event.joined ? ' · You are in' : ''}`));
    const full = event.attendees >= event.capacity;
    const ended = new Date(`${event.day}T${event.time}`) < new Date();
    const button = element('button', event.joined ? 'Leave meetup' : ended ? 'Meetup ended' : full ? 'Meetup full' : 'Join meetup');
    button.disabled = !event.joined && (full || ended);
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        const result = await api(`/api/meetups/${event.id}/${event.joined ? 'leave' : 'join'}`, {});
        await refresh(false); status(result.message);
      } catch (error) { status(error.message, true); button.disabled = false; }
    });
    card.append(button); target.append(card);
  }
}
async function refresh(fillProfile = true) {
  state = await api('/api/state');
  if (fillProfile) for (const [key, value] of Object.entries(state.profile)) {
    const field = $('#profile-form').elements.namedItem(key); if (field) field.value = value;
  }
  renderMatches(); renderEvents();
  $('#interest-count').textContent = `${state.interest_count} unique email(s) recorded locally. Demo profiles are not included.`;
}
function bindForm(selector, path, transform = data => data, reset = false) {
  const form = $(selector);
  form.addEventListener('submit', async event => {
    event.preventDefault(); const button = form.querySelector('button'); button.disabled = true;
    try {
      const result = await api(path, transform(Object.fromEntries(new FormData(form))));
      if (reset) form.reset();
      await refresh(false); status(result.message);
    } catch (error) { status(error.message || 'Could not connect. Check that the Python server is running.', true); }
    finally { button.disabled = false; }
  });
}
bindForm('#profile-form', '/api/profile');
bindForm('#meetup-form', '/api/meetups', data => ({ ...data, capacity: Number(data.capacity) }), true);
bindForm('#interest-form', '/api/interest', data => ({ ...data, consent: data.consent === 'on' }), true);
$('#match-filter').addEventListener('change', renderMatches);
const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1);
$('#meetup-form [name="day"]').min = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth()+1).padStart(2,'0')}-${String(tomorrow.getDate()).padStart(2,'0')}`;
refresh().then(() => status('')).catch(() => status('Could not load the prototype. Start the Python server, then reload this page.', true));
