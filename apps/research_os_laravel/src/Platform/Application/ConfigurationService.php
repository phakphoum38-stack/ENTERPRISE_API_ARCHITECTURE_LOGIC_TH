<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Application;
final class ConfigurationService {
    public function get(string $key, mixed $default = null): mixed { return config($key, $default); }
}
