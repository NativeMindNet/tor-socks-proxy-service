# Use a minimal Alpine Linux base image
FROM alpine:latest

# Install Tor
# Use 'apk add' for Alpine Linux packages
RUN apk add --no-cache tor

# Expose the default Tor SOCKS port
EXPOSE 9050

# Create a Tor data directory and set appropriate permissions
RUN mkdir -p /var/lib/tor \
    && chown -R tor:tor /var/lib/tor \
    && chmod 0700 /var/lib/tor

# Switch to the 'tor' user for security
USER tor

# Command to run Tor when the container starts
# Tor will look for torrc in /etc/tor/ by default, which can be mounted as a volume
CMD ["tor", "-f", "/var/lib/tor/torrc"]
