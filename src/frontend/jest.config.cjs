/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  roots: ["<rootDir>/app"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/app/$1",
  }
};