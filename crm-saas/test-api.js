#!/usr/bin/env node
const http = require('http');

const baseURL = 'http://localhost:3333';

// Colors for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[36m',
};

// Helper function to make HTTP requests
function makeRequest(method, path, data = null, token = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, baseURL);
    const options = {
      method,
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`;
    }

    const req = http.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(responseData);
          resolve({ status: res.statusCode, data: parsed });
        } catch {
          resolve({ status: res.statusCode, data: responseData });
        }
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }
    req.end();
  });
}

// Test function
async function runTests() {
  console.log(`${colors.blue}🧪 Test du CRM SaaS API${colors.reset}\n`);

  let token = null;

  // Test 1: Health Check
  try {
    console.log('📍 Test Health Check...');
    const health = await makeRequest('GET', '/health');
    if (health.status === 200) {
      console.log(`${colors.green}✅ Health Check OK${colors.reset}`);
      console.log(`   Version: ${health.data.version}`);
      console.log(`   Environment: ${health.data.environment}`);
    } else {
      console.log(`${colors.red}❌ Health Check Failed${colors.reset}`);
    }
  } catch (error) {
    console.log(`${colors.red}❌ Server not responding${colors.reset}`);
    console.log(`   Error: ${error.message}`);
    return;
  }

  // Test 2: Login
  try {
    console.log('\n📍 Test Login...');
    const login = await makeRequest('POST', '/api/auth/login', {
      email: 'admin@test.com',
      password: 'Admin123!',
    });

    if (login.status === 200) {
      console.log(`${colors.green}✅ Login successful${colors.reset}`);
      token = login.data.accessToken;
      console.log(`   User: ${login.data.user.email}`);
      console.log(`   Role: ${login.data.user.role}`);
    } else {
      console.log(`${colors.red}❌ Login failed${colors.reset}`);
      console.log(`   Error: ${login.data.error || login.data.message}`);
    }
  } catch (error) {
    console.log(`${colors.red}❌ Login error${colors.reset}`);
    console.log(`   Error: ${error.message}`);
  }

  // Test 3: Get Companies (requires auth)
  if (token) {
    try {
      console.log('\n📍 Test Get Companies...');
      const companies = await makeRequest('GET', '/api/companies', null, token);

      if (companies.status === 200) {
        console.log(`${colors.green}✅ Companies fetched${colors.reset}`);
        console.log(`   Count: ${companies.data.companies.length}`);
        if (companies.data.companies.length > 0) {
          console.log(`   First: ${companies.data.companies[0].name}`);
        }
      } else {
        console.log(`${colors.red}❌ Failed to fetch companies${colors.reset}`);
      }
    } catch (error) {
      console.log(`${colors.red}❌ Companies error${colors.reset}`);
      console.log(`   Error: ${error.message}`);
    }

    // Test 4: Get Deals Pipeline
    try {
      console.log('\n📍 Test Get Deals Pipeline...');
      const pipeline = await makeRequest('GET', '/api/deals/pipeline', null, token);

      if (pipeline.status === 200) {
        console.log(`${colors.green}✅ Pipeline fetched${colors.reset}`);
        const stages = Object.keys(pipeline.data.pipeline);
        console.log(`   Stages: ${stages.join(', ')}`);
        if (pipeline.data.totals) {
          const totalDeals = Object.values(pipeline.data.totals).reduce(
            (sum, stage) => sum + stage.count,
            0
          );
          console.log(`   Total deals: ${totalDeals}`);
        }
      } else {
        console.log(`${colors.red}❌ Failed to fetch pipeline${colors.reset}`);
      }
    } catch (error) {
      console.log(`${colors.red}❌ Pipeline error${colors.reset}`);
      console.log(`   Error: ${error.message}`);
    }

    // Test 5: Attendance - Get Today
    try {
      console.log('\n📍 Test Get Today\'s Attendance...');
      const attendance = await makeRequest('GET', '/api/attendance/today', null, token);

      if (attendance.status === 200) {
        console.log(`${colors.green}✅ Attendance fetched${colors.reset}`);
        console.log(`   Total punches: ${attendance.data.summary.totalPunches}`);
        console.log(`   Worked time: ${attendance.data.summary.workedTime}`);
      } else {
        console.log(`${colors.red}❌ Failed to fetch attendance${colors.reset}`);
      }
    } catch (error) {
      console.log(`${colors.red}❌ Attendance error${colors.reset}`);
      console.log(`   Error: ${error.message}`);
    }

    // Test 6: Create a ticket
    try {
      console.log('\n📍 Test Create Ticket...');
      const ticket = await makeRequest(
        'POST',
        '/api/tickets',
        {
          subject: 'Test Ticket from API',
          description: 'This is a test ticket created via API tests',
          priority: 'MEDIUM',
        },
        token
      );

      if (ticket.status === 201) {
        console.log(`${colors.green}✅ Ticket created${colors.reset}`);
        console.log(`   Number: ${ticket.data.ticket.number}`);
        console.log(`   ID: ${ticket.data.ticket.id}`);
      } else {
        console.log(`${colors.red}❌ Failed to create ticket${colors.reset}`);
      }
    } catch (error) {
      console.log(`${colors.red}❌ Ticket creation error${colors.reset}`);
      console.log(`   Error: ${error.message}`);
    }
  }

  console.log(`\n${colors.blue}✨ Tests terminés!${colors.reset}\n`);
}

// Check if server is running
function waitForServer(retries = 30) {
  console.log(`${colors.yellow}⏳ En attente du serveur...${colors.reset}`);
  
  return new Promise((resolve, reject) => {
    let attempt = 0;
    
    const checkServer = () => {
      makeRequest('GET', '/health')
        .then(() => {
          console.log(`${colors.green}✅ Serveur prêt!${colors.reset}\n`);
          resolve();
        })
        .catch(() => {
          attempt++;
          if (attempt >= retries) {
            reject(new Error('Le serveur ne répond pas après 30 secondes'));
          } else {
            setTimeout(checkServer, 1000);
          }
        });
    };
    
    checkServer();
  });
}

// Main
waitForServer()
  .then(runTests)
  .catch((error) => {
    console.log(`${colors.red}❌ ${error.message}${colors.reset}`);
    process.exit(1);
  });