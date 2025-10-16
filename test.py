from malware_api import check_hash

# Define your test hash here
TEST_HASH = "5a4eaf32d0659b7901cf0c8414447abf7729f191ee9117afdabbb67d10367f27"

print("Testing Malware Bazaar API Client\n")
print(f"Using test hash: {TEST_HASH}\n")

# Call the function and get the result
result = check_hash(TEST_HASH)

# Display results
print(f"Success: {result['success']}")
print(f"Is Malicious: {result['is_malicious']}")
print(f"Query Status: {result['query_status']}")

if result['is_malicious']:
    print("\n⚠️ MALWARE DETECTED!")
    print("\nMalware Info:")
    for key, value in result['malware_info'].items():
        if value:
            print(f"  {key}: {value}")
elif result['success']:
    print("\n✅ File appears safe")
else:
    print(f"\n❌ Error: {result['error']}")