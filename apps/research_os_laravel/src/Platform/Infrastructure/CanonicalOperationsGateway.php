<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Infrastructure;
use ResearchOS\Platform\Contracts\OperationsGateway;
final class CanonicalOperationsGateway implements OperationsGateway {
    public function __construct(private readonly CanonicalPlatformClient $client, private readonly string $endpoint) {}
    public function snapshot(): array {
        return $this->client->get($this->endpoint);
    }
}
