<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Infrastructure;
use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Contracts\ToolGateway;
final class CanonicalToolGateway implements ToolGateway {
    public function __construct(private readonly CanonicalPlatformClient $client, private readonly string $endpoint) {}
    public function invoke(RequestContext $context, string $tool, array $input): array {
        return $this->client->post($context, $this->endpoint, ['tool'=>$tool,'input'=>$input]);
    }
}
