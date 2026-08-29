import { promises as fs } from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const rootDir = process.cwd();
const appsDir = path.join(rootDir, 'apps');
const overridePath = path.join(rootDir, 'apps/admin/data/site-registry-overrides.json');
const outputPath = path.join(rootDir, 'apps/admin/data/site-registry.json');

const apiRoutes = ['/health', '/openapi.json', '/api/v1/leads', '/api/v1/admin/leads'];

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function walkHtmlFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = await Promise.all(entries.map(async entry => {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return walkHtmlFiles(entryPath);
    if (entry.isFile() && entry.name.endsWith('.html')) return [entryPath];
    return [];
  }));
  return files.flat();
}

function toRoute(filePath) {
  const relativePath = path.relative(rootDir, filePath).replaceAll(path.sep, '/');
  if (relativePath === 'index.html') return '/';
  if (relativePath.endsWith('/index.html')) {
    return `/${relativePath.replace(/index\.html$/, '')}`;
  }
  return `/${relativePath}`;
}

function titleCase(value) {
  return value
    .replace(/\.html$/, '')
    .split(/[-_/]+/)
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function defaultCategory(route) {
  if (route.includes('/case-studies/')) return 'case-study';
  if (route.includes('/admin/')) return 'admin';
  if (
    route.includes('photoshop') ||
    route.includes('service-business') ||
    route.includes('photography') ||
    route.includes('wedding')
  ) return 'service';
  if (route.includes('/personal-site/')) return 'portfolio';
  if (route === '/' || route.endsWith('/')) return 'demo';
  return 'demo';
}

function defaultOwner(route, category) {
  if (category === 'admin') return 'Admin';
  if (category === 'portfolio' || category === 'case-study') return 'Portfolio CMS';
  if (route.includes('stocks')) return 'Stocks operations';
  if (route.includes('photoshop')) return 'Robin Retouch Studio';
  if (category === 'service') return 'Service demos';
  return 'Static app';
}

function defaultName(route) {
  if (route === '/') return 'Root redirect';
  const segments = route.split('/').filter(Boolean);
  if (route.endsWith('/')) return titleCase(segments.at(-1) || 'Home');
  return titleCase(segments.at(-1) || 'Page');
}

function defaultDescription(route, category) {
  if (category === 'api') return 'Backend API surface.';
  if (category === 'case-study') return 'Public case-study page.';
  if (category === 'admin') return 'Private admin surface.';
  if (category === 'service') return 'Public service or booking surface.';
  if (category === 'portfolio') return 'Public portfolio surface.';
  return 'Public static application surface.';
}

function buildEntry(route, overrides) {
  const override = overrides[route] || {};
  const category = override.category || defaultCategory(route);
  const visibility = override.visibility || (category === 'admin' ? 'private' : 'public');
  return {
    name: override.name || defaultName(route),
    category,
    visibility,
    route,
    owner: override.owner || defaultOwner(route, category),
    description: override.description || defaultDescription(route, category),
    urlType: override.urlType || 'public',
    method: override.method || 'HEAD',
    checkMode: override.checkMode || null,
    requiresAuth: Boolean(override.requiresAuth),
  };
}

async function main() {
  const overrides = await readJson(overridePath);
  const htmlRoutes = (await walkHtmlFiles(appsDir)).map(toRoute);
  const rootRoutes = [];
  try {
    await fs.access(path.join(rootDir, 'index.html'));
    rootRoutes.push('/');
  } catch {
    // Root index is optional for local experiments.
  }
  const routes = [...new Set([...rootRoutes, ...htmlRoutes, ...apiRoutes])].sort((a, b) => {
    if (a === '/') return -1;
    if (b === '/') return 1;
    return a.localeCompare(b);
  });
  const sites = routes.map(route => buildEntry(route, overrides));
  const payload = {
    source: 'scripts/generate-site-registry.mjs',
    sites,
  };
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(payload, null, 2)}\n`);
  console.log(`Generated ${sites.length} site registry entries at ${path.relative(rootDir, outputPath)}`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
