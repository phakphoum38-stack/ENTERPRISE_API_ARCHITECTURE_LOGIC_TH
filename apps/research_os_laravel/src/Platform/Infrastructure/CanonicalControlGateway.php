<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Infrastructure;
use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Contracts\ControlGateway;
final class CanonicalControlGateway implements ControlGateway {
    public function __construct(private readonly CanonicalPlatformClient $client, private readonly string $endpoint) {}
    public function execute(RequestContext $context, array $command): array {
        return $this->client->post($context, $this->endpoint, $command);
    }
}
